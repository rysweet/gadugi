# LLM Proxy Service Usage Guide

The LLM Proxy Service provides a unified interface to multiple LLM providers with features like load balancing, failover, caching, and cost optimization.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, Google, Azure, HuggingFace, Ollama, Local models
- **Load Balancing**: Round-robin, least-loaded, weighted, fastest-response, cost-optimized strategies
- **Automatic Failover**: Switches to backup providers on failure
- **Response Caching**: Reduces API calls and costs
- **Rate Limiting**: Prevents hitting provider limits
- **Streaming Support**: Real-time token streaming
- **Cost Tracking**: Monitors usage and costs per provider

## Installation

```bash
# Install required dependencies
pip install openai anthropic  # Optional provider libraries
```

## Basic Usage

### 1. Initialize the Service

```python
from llm_proxy_service import LLMProxyService, LoadBalanceStrategy

# Create service instance
service = LLMProxyService(
    cache_size=1000,          # Number of cached responses
    cache_ttl=3600,           # Cache time-to-live in seconds
    load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN,
    enable_failover=True,
    max_retries=3
)

# Start the service
await service.start()
```

### 2. Simple Text Completion

```python
from llm_proxy_service import create_completion_request

# Create a completion request
request = create_completion_request(
    prompt="Explain quantum computing in simple terms",
    model="gpt-3.5-turbo",  # or "claude-3", "gemini-pro", etc.
    temperature=0.7,
    max_tokens=200
)

# Generate completion
response = await service.generate_completion(request)
print(response.content)
```

### 3. Chat Conversation

```python
from llm_proxy_service import create_chat_request

# Create a chat request
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the weather like?"}
]

request = create_chat_request(
    messages=messages,
    model="gpt-4",
    temperature=0.5,
    max_tokens=100
)

# Get response
response = await service.generate_completion(request)
print(response.content)
```

### 4. Streaming Responses

```python
# Enable streaming in request
request = create_completion_request(
    prompt="Write a short story about a robot",
    model="gpt-3.5-turbo"
)
request.stream = True

# Stream the response
async for chunk in service.generate_streaming_completion(request):
    print(chunk.content, end="", flush=True)
```

## Advanced Usage

### Configure Multiple Providers

```python
from llm_proxy_service import ModelConfig, LLMProvider, ModelCapability

# Configure OpenAI
openai_config = ModelConfig(
    provider=LLMProvider.OPENAI,
    model_name="gpt-4",
    api_key="your-openai-key",  # Or use environment variable
    capabilities=[
        ModelCapability.CHAT_COMPLETION,
        ModelCapability.FUNCTION_CALLING
    ],
    max_tokens=4000,
    cost_per_1k_tokens=0.03,
    rate_limit=60,  # requests per minute
    priority=1
)

# Configure Anthropic
anthropic_config = ModelConfig(
    provider=LLMProvider.ANTHROPIC,
    model_name="claude-3-sonnet",
    api_key="your-anthropic-key",
    capabilities=[
        ModelCapability.CHAT_COMPLETION,
        ModelCapability.CODE_COMPLETION
    ],
    max_tokens=100000,
    cost_per_1k_tokens=0.015,
    rate_limit=50,
    priority=2
)

# Register providers
service.register_provider("openai", OpenAIProvider(openai_config))
service.register_provider("anthropic", AnthropicProvider(anthropic_config))
```

### Load Balancing Strategies

```python
# Round Robin - Distributes evenly
service = LLMProxyService(
    load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN
)

# Least Loaded - Routes to provider with fewest active requests
service = LLMProxyService(
    load_balance_strategy=LoadBalanceStrategy.LEAST_LOADED
)

# Cost Optimized - Routes to cheapest available provider
service = LLMProxyService(
    load_balance_strategy=LoadBalanceStrategy.COST_OPTIMIZED
)

# Fastest Response - Routes to provider with best latency
service = LLMProxyService(
    load_balance_strategy=LoadBalanceStrategy.FASTEST_RESPONSE
)
```

### Function Calling

```python
# Define functions for the model to use
functions = [
    {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            }
        }
    }
]

request = create_chat_request(
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    model="gpt-4",
    functions=functions
)

response = await service.generate_completion(request)
if response.function_call:
    print(f"Function: {response.function_call['name']}")
    print(f"Arguments: {response.function_call['arguments']}")
```

### Monitoring and Statistics

```python
# Get service statistics
stats = service.get_service_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Total cost: ${stats['total_cost']:.2f}")

# Health check
health = await service.health_check()
print(f"Service status: {health['status']}")
for provider, status in health['providers'].items():
    print(f"  {provider}: {status}")

# Get provider metrics
for provider_name in service.list_providers():
    metrics = service.get_provider_metrics(provider_name)
    print(f"{provider_name}:")
    print(f"  Requests: {metrics['request_count']}")
    print(f"  Avg latency: {metrics['avg_latency']:.2f}s")
    print(f"  Error rate: {metrics['error_rate']:.2%}")
```

## Environment Variables

The service supports configuration via environment variables:

```bash
# Provider API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# Service Configuration
export LLM_PROXY_CACHE_SIZE="1000"
export LLM_PROXY_CACHE_TTL="3600"
export LLM_PROXY_MAX_RETRIES="3"
export LLM_PROXY_LOAD_BALANCE="ROUND_ROBIN"
```

## Running as a Service

### Standalone Mode

```bash
# Run the service directly
python -m llm_proxy_service

# Or with custom configuration
python -m llm_proxy_service --port 8080 --cache-size 2000
```

### Integration with Gadugi

The LLM Proxy is automatically available when running Gadugi:

```python
# In any Gadugi agent or service
from gadugi.services.llm_proxy import get_llm_service

llm = await get_llm_service()
response = await llm.generate_completion(request)
```

## Error Handling

```python
from llm_proxy_service import LLMProxyError

try:
    response = await service.generate_completion(request)
except LLMProxyError as e:
    print(f"LLM Proxy error: {e}")
    # Service will automatically retry with failover
```

## Best Practices

1. **Use Caching**: Enable caching for repetitive queries to reduce costs
2. **Set Appropriate Timeouts**: Configure timeouts based on your use case
3. **Monitor Costs**: Regularly check service statistics to track spending
4. **Configure Failover**: Set up multiple providers for reliability
5. **Use Streaming**: For long responses, use streaming to improve UX
6. **Rate Limiting**: Configure rate limits to avoid provider throttling

## Example: Complete Application

```python
import asyncio
from llm_proxy_service import (
    LLMProxyService,
    LoadBalanceStrategy,
    create_chat_request
)

async def chat_assistant():
    """Simple chat assistant using LLM Proxy."""
    
    # Initialize service
    service = LLMProxyService(
        cache_size=500,
        load_balance_strategy=LoadBalanceStrategy.COST_OPTIMIZED,
        enable_failover=True
    )
    
    await service.start()
    
    try:
        conversation = []
        print("Chat Assistant Ready! (type 'quit' to exit)")
        
        while True:
            # Get user input
            user_input = input("\nYou: ")
            if user_input.lower() == 'quit':
                break
            
            # Add to conversation
            conversation.append({"role": "user", "content": user_input})
            
            # Create request
            request = create_chat_request(
                messages=conversation,
                model="gpt-3.5-turbo",
                temperature=0.7
            )
            
            # Get response
            response = await service.generate_completion(request)
            print(f"\nAssistant: {response.content}")
            
            # Add to conversation history
            conversation.append({
                "role": "assistant", 
                "content": response.content
            })
            
            # Show stats periodically
            if len(conversation) % 10 == 0:
                stats = service.get_service_stats()
                print(f"\n[Stats] Requests: {stats['total_requests']}, "
                      f"Cost: ${stats['total_cost']:.2f}")
    
    finally:
        await service.stop()
        print("\nGoodbye!")

# Run the assistant
if __name__ == "__main__":
    asyncio.run(chat_assistant())
```

## Troubleshooting

### Provider Not Available
```python
# Check if provider is available
if service.is_provider_available("openai"):
    # Use OpenAI
else:
    # Fallback to another provider
```

### Cache Issues
```python
# Clear cache if needed
service.response_cache.clear()

# Disable cache for specific request
request.cache_enabled = False
```

### Rate Limiting
```python
# Check rate limit status
limits = service.get_rate_limit_status("openai")
print(f"Remaining: {limits['remaining']}/{limits['limit']}")
```

## API Reference

### Core Classes
- `LLMProxyService`: Main service class
- `LLMRequest`: Request object
- `LLMResponse`: Response object
- `ModelConfig`: Model configuration
- `LLMProvider`: Provider enumeration
- `LoadBalanceStrategy`: Load balancing strategies

### Key Methods
- `generate_completion()`: Generate single completion
- `generate_streaming_completion()`: Stream completion
- `register_provider()`: Add new provider
- `get_service_stats()`: Get usage statistics
- `health_check()`: Check service health

For more details, see the source code documentation in `llm_proxy_service.py`.