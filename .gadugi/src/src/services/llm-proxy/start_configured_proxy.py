#!/usr/bin/env python3
"""Start LLM Proxy with existing .env configuration."""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Load environment from .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
    print(f"✅ Loaded configuration from {env_file}")
else:
    print(f"❌ No .env file found at {env_file}")
    sys.exit(1)

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"llm_proxy_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


async def main():
    """Start the LLM Proxy with Azure configuration."""

    logger.info("=" * 60)
    logger.info("Starting LLM Proxy Service")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    try:
        from llm_proxy_service import LLMProxyService, LoadBalanceStrategy

        # Create service
        service = LLMProxyService(
            cache_size=int(os.getenv("LLM_PROXY_CACHE_SIZE", "1000")),
            cache_ttl=int(os.getenv("LLM_PROXY_CACHE_TTL", "3600")),
            load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN,
            enable_failover=False,
        )

        # Configure Azure OpenAI if available
        if os.getenv("AZURE_OPENAI_API_KEY"):
            logger.info("Configuring Azure OpenAI provider")
            logger.info(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
            logger.info(f"Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")

            from llm_proxy_service import ModelConfig, LLMProvider, ModelCapability

            azure_config = ModelConfig(
                provider=LLMProvider.AZURE,
                model_name="gpt-4",
                capabilities=[
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                cost_per_token=0.03,
                rate_limit_rpm=60,
                rate_limit_tpm=90000,
                context_window=8192,
                supports_streaming=True,
                supports_functions=True,
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            )

            # Register the Azure configuration
            service.register_model_config("azure-gpt-4", azure_config)
            logger.info("Azure OpenAI provider registered successfully")

        # Start service without initializing default providers
        service.running = False  # Ensure it's not already marked as running
        logger.info("Starting service...")

        # Manually start without default providers
        service.running = True
        service.cleanup_task = asyncio.create_task(service._cleanup_loop())
        logger.info("Service started without default providers")
        logger.info("LLM Proxy Service started successfully")
        logger.info(f"Port: {os.getenv('LLM_PROXY_PORT', '8080')}")

        print("\n" + "=" * 60)
        print("✅ LLM Proxy Service Started Successfully!")
        print("=" * 60)
        print("\n📌 Service Information:")
        print(f"   PID: {os.getpid()}")
        print(f"   Port: {os.getenv('LLM_PROXY_PORT', '8080')}")
        print("   Provider: Azure OpenAI")
        print(f"   Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
        print("\n📁 Log File:")
        print(f"   {log_file}")
        print("\n📊 To monitor logs:")
        print(f"   tail -f {log_file}")
        print("\n🛑 To stop service:")
        print(f"   Press Ctrl+C or kill {os.getpid()}")
        print("=" * 60)

        # Keep running
        while True:
            await asyncio.sleep(60)
            stats = service.get_service_stats()
            logger.info(f"Stats - Requests: {stats.get('total_requests', 0)}")

    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"❌ Import error: {e}")
        print("Make sure llm_proxy_service.py is properly configured")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
        print(f"❌ Service error: {e}")
    finally:
        try:
            await service.stop()  # type: ignore[assignment]
            logger.info("Service stopped")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
