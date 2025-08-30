from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
import uuid
from typing import Optional

from src.core.config import config  # type: ignore
from src.core.logging import logger  # type: ignore
from src.core.client import OpenAIClient  # type: ignore
from src.models.claude import ClaudeMessagesRequest, ClaudeTokenCountRequest  # type: ignore
from src.conversion.request_converter import convert_claude_to_openai  # type: ignore
from src.conversion.response_converter import (  # type: ignore
    convert_openai_to_claude_response,
    convert_openai_streaming_to_claude_with_cancellation,
)
from src.core.model_manager import model_manager  # type: ignore

router = APIRouter()


@router.get("/health")
async def health_check():  # type: ignore[misc]
    """Comprehensive health check endpoint with upstream validation."""
    import httpx

    health_status = {
        "service": "claude-code-proxy",
        "proxy_status": "healthy",
        "upstream_status": "unknown",
        "configuration": {
            "provider": "unknown",
            "endpoint": config.openai_base_url,
            "models": {
                "big": config.big_model,
                "middle": config.middle_model,
                "small": config.small_model,
            },
        },
        "errors": [],
        "instructions": [],
    }

    # Check basic configuration
    if not config.openai_api_key:
        health_status["proxy_status"] = "error"
        health_status["errors"].append("No API key configured")
        health_status["instructions"].append(
            "Run: cd .claude/services/llm-proxy && uv run python configure_and_start_proxy.py --configure"
        )
        return JSONResponse(status_code=503, content=health_status)

    # Identify provider type
    if "azure.com" in config.openai_base_url.lower():
        health_status["configuration"]["provider"] = "Azure OpenAI"
    elif "openai.com" in config.openai_base_url.lower():
        health_status["configuration"]["provider"] = "OpenAI"
    elif (
        "localhost" in config.openai_base_url.lower()
        or "127.0.0.1" in config.openai_base_url
    ):
        health_status["configuration"]["provider"] = "Ollama (Local)"
    else:
        health_status["configuration"]["provider"] = "Custom OpenAI-compatible"

    # Test upstream connection
    try:
        # Different validation based on provider
        if "azure.com" in config.openai_base_url.lower():
            # Azure OpenAI validation
            test_url = f"{config.openai_base_url}/chat/completions?api-version={config.azure_api_version or '2024-02-15-preview'}"
            headers = {"api-key": config.openai_api_key}

            # Simple test request
            test_payload = {
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
                "temperature": 0,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    test_url, json=test_payload, headers=headers, timeout=10
                )

                if response.status_code == 404:
                    health_status["upstream_status"] = "error"
                    health_status["errors"].append(
                        "Azure OpenAI endpoint not found (404)"
                    )
                    health_status["instructions"].extend(
                        [
                            "Verify your Azure OpenAI configuration:",
                            f"  - Endpoint: {config.openai_base_url}",
                            "  - Deployment name in URL is correct",
                            f"  - API version: {config.azure_api_version or '2024-02-15-preview'}",
                            "",
                            "Common issues:",
                            "  1. Wrong deployment name in URL",
                            "  2. Deployment not yet created in Azure",
                            "  3. Incorrect API version",
                            "",
                            "Re-configure with: uv run python configure_and_start_proxy.py --configure",
                        ]
                    )
                elif response.status_code == 401:
                    health_status["upstream_status"] = "error"
                    health_status["errors"].append(
                        "Azure OpenAI authentication failed (401)"
                    )
                    health_status["instructions"].extend(
                        [
                            "Your API key is invalid or expired.",
                            "Get a new key from Azure Portal and reconfigure.",
                        ]
                    )
                elif response.status_code == 429:
                    health_status["upstream_status"] = "warning"
                    health_status["errors"].append("Rate limit reached")
                    health_status["instructions"].append(
                        "Consider using scheduled shutdown to manage rate limits"
                    )
                elif response.status_code == 200:
                    health_status["upstream_status"] = "healthy"
                else:
                    health_status["upstream_status"] = "error"
                    health_status["errors"].append(
                        f"Unexpected response: {response.status_code}"
                    )

        elif "openai.com" in config.openai_base_url.lower():
            # OpenAI validation
            test_url = f"{config.openai_base_url}/models"
            headers = {"Authorization": f"Bearer {config.openai_api_key}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    health_status["upstream_status"] = "healthy"
                elif response.status_code == 401:
                    health_status["upstream_status"] = "error"
                    health_status["errors"].append("OpenAI API key invalid")
                    health_status["instructions"].append(
                        "Check your OpenAI API key and reconfigure"
                    )
                else:
                    health_status["upstream_status"] = "error"
                    health_status["errors"].append(
                        f"OpenAI API error: {response.status_code}"
                    )

        else:
            # Generic OpenAI-compatible endpoint
            health_status["upstream_status"] = "assumed-healthy"
            health_status["instructions"].append(
                "Custom endpoint - unable to validate automatically"
            )

    except httpx.ConnectError:
        health_status["upstream_status"] = "error"
        health_status["errors"].append("Cannot connect to upstream API")
        health_status["instructions"].extend(
            [
                f"Failed to connect to: {config.openai_base_url}",
                "Check your network connection and endpoint URL",
            ]
        )
    except httpx.TimeoutException:
        health_status["upstream_status"] = "error"
        health_status["errors"].append("Upstream API timeout")
        health_status["instructions"].append(
            "The API endpoint is not responding - check if service is running"
        )
    except Exception as e:
        health_status["upstream_status"] = "error"
        health_status["errors"].append(f"Validation error: {str(e)}")
        health_status["instructions"].append(
            "Check logs for details: ~/.claude-proxy.log"
        )

    # Set overall status
    if health_status["upstream_status"] == "error":
        health_status["proxy_status"] = "degraded"
        return JSONResponse(status_code=503, content=health_status)
    elif health_status["upstream_status"] == "warning":
        return JSONResponse(status_code=200, content=health_status)
    else:
        return JSONResponse(status_code=200, content=health_status)


openai_client = OpenAIClient(
    config.openai_api_key,  # type: ignore[assignment]
    config.openai_base_url,
    config.request_timeout,
    api_version=config.azure_api_version,
)


async def validate_api_key(
    x_api_key: Optional[str] = Header(None), authorization: Optional[str] = Header(None)
):  # type: ignore
    """Validate the client's API key from either x-api-key header or Authorization header."""
    client_api_key = None

    # Extract API key from headers
    if x_api_key:
        client_api_key = x_api_key
    elif authorization and authorization.startswith("Bearer "):
        client_api_key = authorization.replace("Bearer ", "")

    # Skip validation if ANTHROPIC_API_KEY is not set in the environment
    if not config.anthropic_api_key:
        return

    # Validate the client API key
    if not client_api_key or not config.validate_client_api_key(client_api_key):
        logger.warning("Invalid API key provided by client")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Please provide a valid Anthropic API key.",
        )


@router.post("/v1/messages")
async def create_message(
    request: ClaudeMessagesRequest,
    http_request: Request,
    _: None = Depends(validate_api_key),
):  # type: ignore
    try:
        # Log incoming request details (without message content for privacy)
        import logging

        request_logger = logging.getLogger("proxy.requests")
        request_logger.info("[ENDPOINT] Received /v1/messages request")
        request_logger.info(f"[MODEL] {request.model}")
        request_logger.info(f"[MAX_TOKENS] {request.max_tokens}")
        request_logger.info(f"[STREAM] {request.stream}")
        if request.messages:
            request_logger.info(f"[MESSAGE_COUNT] {len(request.messages)}")

        logger.debug(
            f"Processing Claude request: model={request.model}, stream={request.stream}"
        )

        # Generate unique request ID for cancellation tracking
        request_id = str(uuid.uuid4())

        # Convert Claude request to OpenAI format
        openai_request = convert_claude_to_openai(request, model_manager)

        # Check if client disconnected before processing
        if await http_request.is_disconnected():
            raise HTTPException(status_code=499, detail="Client disconnected")

        if request.stream:
            # Streaming response - wrap in error handling
            try:
                openai_stream = openai_client.create_chat_completion_stream(  # type: ignore
                    openai_request, request_id
                )
                return StreamingResponse(  # type: ignore
                    convert_openai_streaming_to_claude_with_cancellation(
                        openai_stream,
                        request,
                        logger,
                        http_request,
                        openai_client,
                        request_id,
                    ),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                    },
                )
            except HTTPException as e:
                # Convert to proper error response for streaming
                logger.error(f"Streaming error: {e.detail}")
                import traceback

                logger.error(traceback.format_exc())
                error_message = openai_client.classify_openai_error(e.detail)
                error_response = {
                    "type": "error",
                    "error": {"type": "api_error", "message": error_message},
                }
                return JSONResponse(status_code=e.status_code, content=error_response)
        else:
            # Non-streaming response
            openai_response = await openai_client.create_chat_completion(  # type: ignore
                openai_request, request_id
            )
            claude_response = convert_openai_to_claude_response(
                openai_response, request
            )
            return claude_response
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        logger.error(f"Unexpected error processing request: {e}")
        logger.error(traceback.format_exc())
        error_message = openai_client.classify_openai_error(str(e))
        raise HTTPException(status_code=500, detail=error_message)


@router.post("/v1/messages/count_tokens")
async def count_tokens(
    request: ClaudeTokenCountRequest, _: None = Depends(validate_api_key)
):  # type: ignore
    try:
        # For token counting, we'll use a simple estimation
        # In a real implementation, you might want to use tiktoken or similar

        total_chars = 0

        # Count system message characters
        if request.system:
            if isinstance(request.system, str):
                total_chars += len(request.system)
            elif isinstance(request.system, list):
                for block in request.system:
                    if hasattr(block, "text"):
                        total_chars += len(block.text)

        # Count message characters
        for msg in request.messages:
            if msg.content is None:
                continue
            elif isinstance(msg.content, str):
                total_chars += len(msg.content)
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, "text") and block.text is not None:  # type: ignore[attr-defined]
                        total_chars += len(block.text)  # type: ignore[attr-defined]

        # Rough estimation: 4 characters per token
        estimated_tokens = max(1, total_chars // 4)

        return {"input_tokens": estimated_tokens}

    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_api_configured": bool(config.openai_api_key),
        "api_key_valid": config.validate_api_key(),
        "client_api_key_validation": bool(config.anthropic_api_key),
    }


@router.get("/test-connection")
async def test_connection():
    """Test API connectivity to OpenAI"""
    try:
        # Simple test request to verify API connectivity
        test_response = await openai_client.create_chat_completion(
            {
                "model": config.small_model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5,
            }
        )

        return {
            "status": "success",
            "message": "Successfully connected to OpenAI API",
            "model_used": config.small_model,
            "timestamp": datetime.now().isoformat(),
            "response_id": test_response.get("id", "unknown"),
        }

    except Exception as e:
        logger.error(f"API connectivity test failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "failed",
                "error_type": "API Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
                "suggestions": [
                    "Check your OPENAI_API_KEY is valid",
                    "Verify your API key has the necessary permissions",
                    "Check if you have reached rate limits",
                ],
            },
        )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Claude-to-OpenAI API Proxy v1.0.0",
        "status": "running",
        "config": {
            "openai_base_url": config.openai_base_url,
            "max_tokens_limit": config.max_tokens_limit,
            "api_key_configured": bool(config.openai_api_key),
            "client_api_key_validation": bool(config.anthropic_api_key),
            "big_model": config.big_model,
            "small_model": config.small_model,
        },
        "endpoints": {
            "messages": "/v1/messages",
            "count_tokens": "/v1/messages/count_tokens",
            "health": "/health",
            "test_connection": "/test-connection",
        },
    }
