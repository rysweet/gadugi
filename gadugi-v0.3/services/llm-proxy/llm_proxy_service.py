#!/usr/bin/env python3
"""LLM Proxy Service for Gadugi v0.3.

Provides provider abstraction and unified access to multiple LLM providers.
Handles load balancing, failover, rate limiting, caching, and cost optimization.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Tuple

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

# Optional provider imports with fallbacks
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    # import requests  # Commented out to fix unused import lint error
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class LLMProvider(Enum):
    """LLM provider enumeration."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    LOCAL = "local"
    MOCK = "mock"


class ModelCapability(Enum):
    """Model capability enumeration."""

    TEXT_GENERATION = "text_generation"
    CHAT_COMPLETION = "chat_completion"
    CODE_COMPLETION = "code_completion"
    FUNCTION_CALLING = "function_calling"
    EMBEDDINGS = "embeddings"
    IMAGE_ANALYSIS = "image_analysis"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    FINE_TUNING = "fine_tuning"


class RequestType(Enum):
    """Request type enumeration."""

    COMPLETION = "completion"
    CHAT = "chat"
    EMBEDDING = "embedding"
    FUNCTION_CALL = "function_call"
    STREAM = "stream"


class LoadBalanceStrategy(Enum):
    """Load balancing strategy enumeration."""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED = "weighted"
    FASTEST_RESPONSE = "fastest_response"
    COST_OPTIMIZED = "cost_optimized"
    RANDOM = "random"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    provider: LLMProvider
    model_name: str
    capabilities: list[ModelCapability]
    max_tokens: int
    cost_per_token: float
    rate_limit_rpm: int
    rate_limit_tpm: int
    context_window: int
    supports_streaming: bool = True
    supports_functions: bool = False
    api_endpoint: str | None = None
    api_key: str | None = None
    weight: float = 1.0
    priority: int = 1


@dataclass
class LLMRequest:
    """Represents an LLM request."""

    id: str
    type: RequestType
    provider: LLMProvider | None = None
    model: str | None = None
    messages: list[dict[str, str]] | None = None
    prompt: str | None = None
    max_tokens: int | None = None
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: list[str] | None = None
    stream: bool = False
    functions: list[dict[str, Any]] | None = None
    function_call: str | None = None
    metadata: dict[str, Any] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class LLMResponse:
    """Represents an LLM response."""

    id: str
    request_id: str
    provider: LLMProvider
    model: str
    content: str
    usage: dict[str, int]
    finish_reason: str
    function_calls: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = None
    created_at: datetime = None
    response_time: float = 0.0

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ProviderStats:
    """Statistics for a provider."""

    provider: LLMProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    last_request_time: datetime | None = None
    rate_limit_hits: int = 0
    error_rate: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


@dataclass
class CacheEntry:
    """Cache entry for LLM responses."""

    key: str
    response: LLMResponse
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime = None
    ttl: int = 3600  # seconds

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl)


class RateLimiter:
    """Rate limiting implementation."""

    def __init__(self, requests_per_minute: int, tokens_per_minute: int) -> None:
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times: list[datetime] = []
        self.token_usage: list[Tuple[datetime, int]] = []
        self.lock = threading.Lock()

    def can_make_request(self, estimated_tokens: int = 0) -> bool:
        """Check if a request can be made within rate limits."""
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=1)

            # Remove old entries
            self.request_times = [t for t in self.request_times if t > cutoff]
            self.token_usage = [(t, tokens) for t, tokens in self.token_usage if t > cutoff]

            # Check request rate limit
            if len(self.request_times) >= self.requests_per_minute:
                return False

            # Check token rate limit
            total_tokens = sum(tokens for _, tokens in self.token_usage)
            return not total_tokens + estimated_tokens > self.tokens_per_minute

    def record_request(self, tokens_used: int = 0) -> None:
        """Record a request for rate limiting."""
        with self.lock:
            now = datetime.now()
            self.request_times.append(now)
            if tokens_used > 0:
                self.token_usage.append((now, tokens_used))


class LLMProviderBase(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self.stats = ProviderStats(provider=config.provider)
        self.rate_limiter = RateLimiter(config.rate_limit_rpm, config.rate_limit_tpm)
        self.logger = logging.getLogger(f"llm_provider_{config.provider.value}")

    @abstractmethod
    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate completion for the request."""
        ...

    @abstractmethod
    async def generate_streaming_completion(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        """Generate streaming completion for the request."""
        ...

    def can_handle_request(self, request: LLMRequest) -> bool:
        """Check if provider can handle the request."""
        if request.type == RequestType.FUNCTION_CALL and not self.config.supports_functions:
            return False

        if request.stream and not self.config.supports_streaming:
            return False

        # Check rate limits
        estimated_tokens = request.max_tokens or 100
        if not self.rate_limiter.can_make_request(estimated_tokens):
            self.stats.rate_limit_hits += 1
            return False

        return True

    def update_stats(self, request: LLMRequest, response: LLMResponse, success: bool) -> None:
        """Update provider statistics."""
        self.stats.total_requests += 1
        self.stats.last_request_time = datetime.now()

        if success:
            self.stats.successful_requests += 1
            if response.usage:
                tokens = response.usage.get("total_tokens", 0)
                self.stats.total_tokens += tokens
                self.stats.total_cost += tokens * self.config.cost_per_token
                self.rate_limiter.record_request(tokens)

            # Update average response time
            if self.stats.total_requests > 0:
                self.stats.average_response_time = (
                    self.stats.average_response_time * (self.stats.successful_requests - 1)
                    + response.response_time
                ) / self.stats.successful_requests
        else:
            self.stats.failed_requests += 1

        # Update error rate
        if self.stats.total_requests > 0:
            self.stats.error_rate = self.stats.failed_requests / self.stats.total_requests


class OpenAIProvider(LLMProviderBase):
    """OpenAI provider implementation."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        if OPENAI_AVAILABLE:
            self.client = openai.AsyncOpenAI(api_key=config.api_key)
        else:
            self.client = None

    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using OpenAI API."""
        if not self.client:
            msg = "OpenAI client not available"
            raise Exception(msg)

        start_time = time.time()

        try:
            if request.messages:
                # Chat completion
                response = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=request.messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    frequency_penalty=request.frequency_penalty,
                    presence_penalty=request.presence_penalty,
                    stop=request.stop_sequences,
                    functions=request.functions,
                    function_call=request.function_call,
                )

                content = response.choices[0].message.content or ""
                function_calls = []
                if (
                    hasattr(response.choices[0].message, "function_call")
                    and response.choices[0].message.function_call
                ):
                    function_calls = [response.choices[0].message.function_call]

            else:
                # Text completion
                response = await self.client.completions.create(
                    model=self.config.model_name,
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    frequency_penalty=request.frequency_penalty,
                    presence_penalty=request.presence_penalty,
                    stop=request.stop_sequences,
                )

                content = response.choices[0].text
                function_calls = None

            response_time = time.time() - start_time

            llm_response = LLMResponse(
                id=str(uuid.uuid4()),
                request_id=request.id,
                provider=self.config.provider,
                model=self.config.model_name,
                content=content,
                usage=response.usage.model_dump() if response.usage else {},
                finish_reason=response.choices[0].finish_reason,
                function_calls=function_calls,
                response_time=response_time,
            )

            self.update_stats(request, llm_response, True)
            return llm_response

        except Exception as e:
            response_time = time.time() - start_time
            self.logger.exception(f"OpenAI request failed: {e}")

            error_response = LLMResponse(
                id=str(uuid.uuid4()),
                request_id=request.id,
                provider=self.config.provider,
                model=self.config.model_name,
                content=f"Error: {e!s}",
                usage={},
                finish_reason="error",
                response_time=response_time,
            )

            self.update_stats(request, error_response, False)
            raise

    async def generate_streaming_completion(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        """Generate streaming completion using OpenAI API."""
        if not self.client:
            msg = "OpenAI client not available"
            raise Exception(msg)

        try:
            if request.messages:
                stream = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=request.messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    stream=True,
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                stream = await self.client.completions.create(
                    model=self.config.model_name,
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    stream=True,
                )

                async for chunk in stream:
                    if chunk.choices[0].text:
                        yield chunk.choices[0].text

        except Exception as e:
            self.logger.exception(f"OpenAI streaming request failed: {e}")
            raise


class AnthropicProvider(LLMProviderBase):
    """Anthropic provider implementation."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        if ANTHROPIC_AVAILABLE:
            self.client = anthropic.AsyncAnthropic(api_key=config.api_key)
        else:
            self.client = None

    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using Anthropic API."""
        if not self.client:
            msg = "Anthropic client not available"
            raise Exception(msg)

        start_time = time.time()

        try:
            # Convert messages to Anthropic format
            messages = []
            if request.messages:
                for msg in request.messages:
                    if msg["role"] in ["user", "assistant"]:
                        messages.append(
                            {"role": msg["role"], "content": msg["content"]},
                        )

            response = await self.client.messages.create(
                model=self.config.model_name,
                messages=messages or [{"role": "user", "content": request.prompt or ""}],
                max_tokens=request.max_tokens or 1000,
                temperature=request.temperature,
                top_p=request.top_p,
                stop_sequences=request.stop_sequences,
            )

            response_time = time.time() - start_time

            llm_response = LLMResponse(
                id=str(uuid.uuid4()),
                request_id=request.id,
                provider=self.config.provider,
                model=self.config.model_name,
                content=response.content[0].text if response.content else "",
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                finish_reason=response.stop_reason,
                response_time=response_time,
            )

            self.update_stats(request, llm_response, True)
            return llm_response

        except Exception as e:
            response_time = time.time() - start_time
            self.logger.exception(f"Anthropic request failed: {e}")

            error_response = LLMResponse(
                id=str(uuid.uuid4()),
                request_id=request.id,
                provider=self.config.provider,
                model=self.config.model_name,
                content=f"Error: {e!s}",
                usage={},
                finish_reason="error",
                response_time=response_time,
            )

            self.update_stats(request, error_response, False)
            raise

    async def generate_streaming_completion(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        """Generate streaming completion using Anthropic API."""
        if not self.client:
            msg = "Anthropic client not available"
            raise Exception(msg)

        try:
            messages = []
            if request.messages:
                for msg in request.messages:
                    if msg["role"] in ["user", "assistant"]:
                        messages.append(
                            {"role": msg["role"], "content": msg["content"]},
                        )

            stream = await self.client.messages.create(
                model=self.config.model_name,
                messages=messages or [{"role": "user", "content": request.prompt or ""}],
                max_tokens=request.max_tokens or 1000,
                temperature=request.temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text

        except Exception as e:
            self.logger.exception(f"Anthropic streaming request failed: {e}")
            raise


class MockProvider(LLMProviderBase):
    """Mock provider for testing."""

    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate mock completion."""
        await asyncio.sleep(0.1)  # Simulate network delay

        start_time = time.time()

        # Generate mock content
        if request.messages:
            content = f"Mock response to: {request.messages[-1]['content'][:50]}..."
        else:
            content = f"Mock response to: {(request.prompt or '')[:50]}..."

        response_time = time.time() - start_time

        llm_response = LLMResponse(
            id=str(uuid.uuid4()),
            request_id=request.id,
            provider=self.config.provider,
            model=self.config.model_name,
            content=content,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            response_time=response_time,
        )

        self.update_stats(request, llm_response, True)
        return llm_response

    async def generate_streaming_completion(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        """Generate mock streaming completion."""
        content = "This is a mock streaming response. "
        words = content.split()

        for word in words:
            await asyncio.sleep(0.05)  # Simulate streaming delay
            yield word + " "


class ResponseCache:
    """LRU cache for LLM responses."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: dict[str, CacheEntry] = {}
        self.access_order: list[str] = []
        self.lock = threading.Lock()

    def _generate_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request."""
        # Create deterministic key based on request parameters
        key_data = {
            "model": request.model,
            "messages": request.messages,
            "prompt": request.prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, request: LLMRequest) -> LLMResponse | None:
        """Get cached response if available."""
        if request.stream:  # Don't cache streaming requests
            return None

        key = self._generate_cache_key(request)

        with self.lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]

            # Check if expired
            if entry.is_expired:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                return None

            # Update access tracking
            entry.access_count += 1
            entry.last_accessed = datetime.now()

            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

            return entry.response

    def put(
        self,
        request: LLMRequest,
        response: LLMResponse,
        ttl: int | None = None,
    ) -> None:
        """Cache response."""
        if request.stream:  # Don't cache streaming requests
            return

        key = self._generate_cache_key(request)
        ttl = ttl or self.default_ttl

        with self.lock:
            # Create cache entry
            entry = CacheEntry(
                key=key,
                response=response,
                created_at=datetime.now(),
                ttl=ttl,
            )

            self.cache[key] = entry
            self.access_order.append(key)

            # Evict least recently used if cache is full
            while len(self.cache) > self.max_size:
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]

    def clear_expired(self) -> None:
        """Clear expired cache entries."""
        with self.lock:
            expired_keys = [key for key, entry in self.cache.items() if entry.is_expired]

            for key in expired_keys:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_ratio": 0.0,  # Would need to track hits/misses
                "expired_entries": sum(1 for entry in self.cache.values() if entry.is_expired),
            }


class LoadBalancer:
    """Load balancer for distributing requests across providers."""

    def __init__(self, strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN) -> None:
        self.strategy = strategy
        self.providers: list[LLMProviderBase] = []
        self.current_index = 0
        self.lock = threading.Lock()

    def add_provider(self, provider: LLMProviderBase) -> None:
        """Add provider to load balancer."""
        self.providers.append(provider)

    def select_provider(self, request: LLMRequest) -> LLMProviderBase | None:
        """Select best provider for request."""
        if not self.providers:
            return None

        # Filter providers that can handle the request
        available_providers = [p for p in self.providers if p.can_handle_request(request)]

        if not available_providers:
            return None

        with self.lock:
            if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
                provider = available_providers[self.current_index % len(available_providers)]
                self.current_index += 1
                return provider

            if self.strategy == LoadBalanceStrategy.LEAST_LOADED:
                # Select provider with lowest request count
                return min(available_providers, key=lambda p: p.stats.total_requests)

            if self.strategy == LoadBalanceStrategy.FASTEST_RESPONSE:
                # Select provider with fastest average response time
                return min(
                    available_providers,
                    key=lambda p: p.stats.average_response_time or float("inf"),
                )

            if self.strategy == LoadBalanceStrategy.COST_OPTIMIZED:
                # Select provider with lowest cost per token
                return min(available_providers, key=lambda p: p.config.cost_per_token)

            if self.strategy == LoadBalanceStrategy.WEIGHTED:
                # Select based on provider weights
                import random

                weights = [p.config.weight for p in available_providers]
                return random.choices(available_providers, weights=weights)[0]

            if self.strategy == LoadBalanceStrategy.RANDOM:
                import random

                return random.choice(available_providers)

            return available_providers[0]


class LLMProxyService:
    """Main LLM Proxy Service."""

    def __init__(
        self,
        cache_size: int = 1000,
        cache_ttl: int = 3600,
        load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
        enable_failover: bool = True,
        max_retries: int = 3,
    ) -> None:
        """Initialize the LLM Proxy Service."""
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self.enable_failover = enable_failover
        self.max_retries = max_retries

        self.logger = self._setup_logging()

        # Core components
        self.response_cache = ResponseCache(cache_size, cache_ttl)
        self.load_balancer = LoadBalancer(load_balance_strategy)

        # Provider registry
        self.providers: dict[str, LLMProviderBase] = {}
        self.model_configs: dict[str, ModelConfig] = {}

        # Service state
        self.running = False
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

        # Thread pool for concurrent requests
        self.executor = ThreadPoolExecutor(max_workers=50)

        # Background tasks
        self.cleanup_task: asyncio.Task | None = None

        self.logger.info("LLM Proxy Service initialized")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the LLM proxy service."""
        logger = logging.getLogger("llm_proxy")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def start(self) -> None:
        """Start the LLM proxy service."""
        if self.running:
            self.logger.warning("LLM proxy service is already running")
            return

        self.running = True
        self.logger.info("Starting LLM proxy service")

        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Initialize default providers if available
        await self._initialize_default_providers()

        self.logger.info("LLM proxy service started successfully")

    async def stop(self) -> None:
        """Stop the LLM proxy service."""
        if not self.running:
            return

        self.logger.info("Stopping LLM proxy service")
        self.running = False

        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.cleanup_task

        # Shutdown executor
        self.executor.shutdown(wait=True)

        self.logger.info("LLM proxy service stopped")

    async def _initialize_default_providers(self) -> None:
        """Initialize default providers if API keys are available."""
        # OpenAI
        if OPENAI_AVAILABLE:
            openai_config = ModelConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                capabilities=[
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                max_tokens=4096,
                cost_per_token=0.002,
                rate_limit_rpm=3500,
                rate_limit_tpm=90000,
                context_window=4096,
                supports_streaming=True,
                supports_functions=True,
                api_key=None,  # Would need to be set from environment
            )
            self.register_model_config("gpt-3.5-turbo", openai_config)

        # Anthropic
        if ANTHROPIC_AVAILABLE:
            anthropic_config = ModelConfig(
                provider=LLMProvider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                capabilities=[ModelCapability.CHAT_COMPLETION],
                max_tokens=4096,
                cost_per_token=0.003,
                rate_limit_rpm=1000,
                rate_limit_tpm=40000,
                context_window=200000,
                supports_streaming=True,
                supports_functions=False,
                api_key=None,  # Would need to be set from environment
            )
            self.register_model_config("claude-3-sonnet", anthropic_config)

        # Mock provider (always available for testing)
        mock_config = ModelConfig(
            provider=LLMProvider.MOCK,
            model_name="mock-model",
            capabilities=[
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.TEXT_GENERATION,
            ],
            max_tokens=2048,
            cost_per_token=0.0,
            rate_limit_rpm=1000,
            rate_limit_tpm=50000,
            context_window=2048,
            supports_streaming=True,
            supports_functions=False,
        )
        self.register_model_config("mock-model", mock_config)

    def register_model_config(self, model_id: str, config: ModelConfig) -> None:
        """Register a model configuration."""
        self.model_configs[model_id] = config

        # Create provider instance
        if config.provider == LLMProvider.OPENAI:
            provider = OpenAIProvider(config)
        elif config.provider == LLMProvider.ANTHROPIC:
            provider = AnthropicProvider(config)
        elif config.provider == LLMProvider.MOCK:
            provider = MockProvider(config)
        else:
            self.logger.warning(f"Unsupported provider: {config.provider}")
            return

        self.providers[model_id] = provider
        self.load_balancer.add_provider(provider)

        self.logger.info(f"Registered model: {model_id} ({config.provider.value})")

    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate completion for request."""
        self.request_count += 1

        # Check cache first
        cached_response = self.response_cache.get(request)
        if cached_response:
            self.cache_hits += 1
            self.logger.debug(f"Cache hit for request {request.id}")
            return cached_response

        self.cache_misses += 1

        # Select provider
        if request.model and request.model in self.providers:
            provider = self.providers[request.model]
        else:
            provider = self.load_balancer.select_provider(request)

        if not provider:
            msg = "No available provider for request"
            raise Exception(msg)

        # Generate response with retries
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = await provider.generate_completion(request)

                # Cache successful response
                self.response_cache.put(request, response, self.cache_ttl)

                return response

            except Exception as e:
                last_exception = e
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")

                if not self.enable_failover or attempt >= self.max_retries - 1:
                    break

                # Try next available provider for failover
                provider = self.load_balancer.select_provider(request)
                if not provider:
                    break

        raise last_exception or Exception("All retry attempts failed")

    async def generate_streaming_completion(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        """Generate streaming completion for request."""
        self.request_count += 1

        # Select provider
        if request.model and request.model in self.providers:
            provider = self.providers[request.model]
        else:
            provider = self.load_balancer.select_provider(request)

        if not provider:
            msg = "No available provider for streaming request"
            raise Exception(msg)

        # Generate streaming response
        try:
            async for chunk in provider.generate_streaming_completion(request):
                yield chunk
        except Exception as e:
            self.logger.exception(f"Streaming request failed: {e}")
            raise

    def get_available_models(self) -> list[dict[str, Any]]:
        """Get list of available models."""
        models = []
        for model_id, config in self.model_configs.items():
            models.append(
                {
                    "id": model_id,
                    "provider": config.provider.value,
                    "name": config.model_name,
                    "capabilities": [cap.value for cap in config.capabilities],
                    "max_tokens": config.max_tokens,
                    "cost_per_token": config.cost_per_token,
                    "context_window": config.context_window,
                    "supports_streaming": config.supports_streaming,
                    "supports_functions": config.supports_functions,
                },
            )

        return models

    def get_provider_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all providers."""
        stats = {}
        for model_id, provider in self.providers.items():
            stats[model_id] = asdict(provider.stats)

        return stats

    def get_service_stats(self) -> dict[str, Any]:
        """Get service-level statistics."""
        cache_stats = self.response_cache.get_stats()

        return {
            "running": self.running,
            "total_requests": self.request_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": self.cache_hits / max(self.request_count, 1),
            "registered_models": len(self.model_configs),
            "active_providers": len(self.providers),
            "cache_stats": cache_stats,
            "load_balance_strategy": self.load_balancer.strategy.value,
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on the service."""
        health_info = {
            "status": "unknown",
            "running": self.running,
            "providers": {},
            "service_stats": self.get_service_stats(),
        }

        if not self.running:
            health_info["status"] = "stopped"
            return health_info

        try:
            # Test each provider with a simple request
            provider_health = {}
            for model_id, provider in self.providers.items():
                try:
                    test_request = LLMRequest(
                        id=f"health-check-{model_id}",
                        type=RequestType.COMPLETION,
                        prompt="Hello",
                        max_tokens=5,
                        temperature=0.0,
                    )

                    if provider.can_handle_request(test_request):
                        # For mock provider, actually test it
                        if isinstance(provider, MockProvider):
                            test_response = await provider.generate_completion(
                                test_request,
                            )
                            provider_health[model_id] = {
                                "status": "healthy",
                                "response_time": test_response.response_time,
                            }
                        else:
                            provider_health[model_id] = {
                                "status": "available",
                                "note": "API key required for full test",
                            }
                    else:
                        provider_health[model_id] = {
                            "status": "rate_limited",
                            "note": "Provider cannot handle requests due to rate limits",
                        }

                except Exception as e:
                    provider_health[model_id] = {"status": "error", "error": str(e)}

            health_info["providers"] = provider_health

            # Overall status
            if all(p["status"] in ["healthy", "available"] for p in provider_health.values()):
                health_info["status"] = "healthy"
            elif any(p["status"] in ["healthy", "available"] for p in provider_health.values()):
                health_info["status"] = "degraded"
            else:
                health_info["status"] = "unhealthy"

        except Exception as e:
            health_info["status"] = "error"
            health_info["error"] = str(e)

        return health_info

    async def _cleanup_loop(self) -> None:
        """Background cleanup task."""
        self.logger.info("Cleanup loop started")

        try:
            while self.running:
                await asyncio.sleep(300)  # Run every 5 minutes

                if not self.running:
                    break

                try:
                    # Clear expired cache entries
                    self.response_cache.clear_expired()
                    self.logger.debug("Cleared expired cache entries")

                except Exception as e:
                    self.logger.exception(f"Error during cleanup: {e}")

        except asyncio.CancelledError:
            self.logger.info("Cleanup loop cancelled")


# Utility functions for common request patterns


def create_chat_request(
    messages: list[dict[str, str]],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> LLMRequest:
    """Create a chat completion request."""
    return LLMRequest(
        id=str(uuid.uuid4()),
        type=RequestType.CHAT,
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_completion_request(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> LLMRequest:
    """Create a text completion request."""
    return LLMRequest(
        id=str(uuid.uuid4()),
        type=RequestType.COMPLETION,
        model=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_function_call_request(
    messages: list[dict[str, str]],
    functions: list[dict[str, Any]],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
) -> LLMRequest:
    """Create a function calling request."""
    return LLMRequest(
        id=str(uuid.uuid4()),
        type=RequestType.FUNCTION_CALL,
        model=model,
        messages=messages,
        functions=functions,
        temperature=temperature,
    )


async def main() -> None:
    """Main function for testing the LLM proxy service."""
    service = LLMProxyService(
        cache_size=100,
        load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN,
        enable_failover=True,
    )

    try:
        await service.start()

        # Test completion request
        request = create_completion_request(
            "What is artificial intelligence?",
            model="mock-model",
            max_tokens=100,
        )

        await service.generate_completion(request)

        # Test chat request
        chat_request = create_chat_request(
            [{"role": "user", "content": "Hello, how are you?"}],
            model="mock-model",
        )

        await service.generate_completion(chat_request)

        # Test streaming
        stream_request = create_completion_request(
            "Tell me a short story",
            model="mock-model",
        )
        stream_request.stream = True

        async for _chunk in service.generate_streaming_completion(stream_request):
            pass

        # Show statistics
        service.get_service_stats()

        # Health check
        await service.health_check()

    except KeyboardInterrupt:
        pass
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
