#!/usr/bin/env python3
"""
Start the Event Router service on port 8000.
This script properly initializes the Flask-based event router service.
"""

import sys
import logging
from pathlib import Path

# Add the service directory to the path for imports
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir))


def setup_logging():
    """Configure logging for the service."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(service_dir / "logs" / "event-router.log", mode="a"),
        ],
    )


def ensure_directories():
    """Ensure required directories exist."""
    dirs_to_create = [
        service_dir / "logs",
        service_dir / "data",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)


def main():
    """Main function to start the Event Router service."""
    print("=" * 60)
    print("🚀 Starting Gadugi Event Router Service")
    print("=" * 60)

    # Setup
    ensure_directories()
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting Event Router service...")

    try:
        # Import and run the main Flask application
        from main import app, initialize_event_system, run_async_in_thread, get_settings

        if app is None:
            logger.error("❌ Flask not available - cannot start service")
            print("❌ Flask not available - cannot start service")
            return 1

        # Initialize the event system
        print("🔧 Initializing event system...")
        run_async_in_thread(initialize_event_system())
        print("✅ Event system initialized")

        # Get settings and start server
        settings = get_settings()

        print(f"🌐 Server starting on {settings.host}:{settings.port}")
        print("📍 Endpoints:")
        print("   - Health check: GET /health")
        print("   - Service info: GET /")
        print("   - Create event: POST /events")
        print("   - List events: GET /events")
        print("   - Filter events: POST /events/filter")
        print("   - Replay events: POST /events/replay")
        print("   - Memory status: GET /memory/status")
        print()
        print("Press Ctrl+C to stop the service")
        print("=" * 60)

        # Start the Flask server
        app.run(
            host=settings.host, port=settings.port, debug=settings.debug, threaded=True
        )

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        print(f"❌ Import error: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        print(f"❌ Failed to start service: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
