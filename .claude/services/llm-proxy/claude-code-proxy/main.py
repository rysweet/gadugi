from fastapi import FastAPI
from src.api.endpoints import router as api_router
import uvicorn
import sys
from src.core.config import config

import logging
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llm-proxy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Claude-to-OpenAI API Proxy", version="1.0.0")

class LogIncomingRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path == "/v1/messages":
            # Read body and preserve it for the next handler
            body_bytes = await request.body()
            body_str = body_bytes.decode(errors='replace')

            # Log the incoming request
            logger.info(f"[PROXY-LOG] Incoming /v1/messages POST request")
            logger.info(f"[PROXY-LOG] Headers: {dict(request.headers)}")
            logger.info(f"[PROXY-LOG] Body (first 2048 chars): {body_str[:2048]}")

            # Try to parse and log key fields
            try:
                body_json = json.loads(body_str)
                logger.info(f"[PROXY-LOG] Model: {body_json.get('model', 'unknown')}")
                logger.info(f"[PROXY-LOG] Max tokens: {body_json.get('max_tokens', 'not specified')}")
                if 'messages' in body_json and body_json['messages']:
                    first_msg = body_json['messages'][0]
                    logger.info(f"[PROXY-LOG] First message role: {first_msg.get('role', 'unknown')}")
                    content_preview = str(first_msg.get('content', ''))[:100]
                    logger.info(f"[PROXY-LOG] First message content preview: {content_preview}")
            except Exception as e:
                logger.warning(f"[PROXY-LOG] Could not parse request body as JSON: {e}")

            # Reconstruct the request with the preserved body
            async def receive():
                return {"type": "http.request", "body": body_bytes}

            request._receive = receive

        response = await call_next(request)
        return response

app.add_middleware(LogIncomingRequestsMiddleware)

app.include_router(api_router)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Claude-to-OpenAI API Proxy v1.0.0")
        print("")
        print("Usage: python src/main.py")
        print("")
        print("Required environment variables:")
        print("  OPENAI_API_KEY - Your OpenAI API key")
        print("")
        print("Optional environment variables:")
        print("  ANTHROPIC_API_KEY - Expected Anthropic API key for client validation")
        print("                      If set, clients must provide this exact API key")
        print(
            f"  OPENAI_BASE_URL - OpenAI API base URL (default: https://api.openai.com/v1)"
        )
        print(f"  BIG_MODEL - Model for opus requests (default: gpt-4o)")
        print(f"  MIDDLE_MODEL - Model for sonnet requests (default: gpt-4o)")
        print(f"  SMALL_MODEL - Model for haiku requests (default: gpt-4o-mini)")
        print(f"  HOST - Server host (default: 0.0.0.0)")
        print(f"  PORT - Server port (default: 8082)")
        print(f"  LOG_LEVEL - Logging level (default: WARNING)")
        print(f"  MAX_TOKENS_LIMIT - Token limit (default: 4096)")
        print(f"  MIN_TOKENS_LIMIT - Minimum token limit (default: 100)")
        print(f"  REQUEST_TIMEOUT - Request timeout in seconds (default: 90)")
        print("")
        print("Model mapping:")
        print(f"  Claude haiku models -> {config.small_model}")
        print(f"  Claude sonnet/opus models -> {config.big_model}")
        sys.exit(0)

    # Configuration summary
    print("🚀 Claude-to-OpenAI API Proxy v1.0.0")
    print(f"✅ Configuration loaded successfully")
    print(f"   OpenAI Base URL: {config.openai_base_url}")
    print(f"   Big Model (opus): {config.big_model}")
    print(f"   Middle Model (sonnet): {config.middle_model}")
    print(f"   Small Model (haiku): {config.small_model}")
    print(f"   Max Tokens Limit: {config.max_tokens_limit}")
    print(f"   Request Timeout: {config.request_timeout}s")
    print(f"   Server: {config.host}:{config.port}")
    print(f"   Client API Key Validation: {'Enabled' if config.anthropic_api_key else 'Disabled'}")
    print("")

    # Parse log level - extract just the first word to handle comments
    log_level = config.log_level.split()[0].lower()

    # Validate and set default if invalid
    valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if log_level not in valid_levels:
        log_level = 'info'

    # Start server
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
