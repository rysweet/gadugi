"""
event-router Service - Flask Implementation with Memory System Integration
Enhanced for Gadugi v0.3 with event persistence, replay, and agent lifecycle tracking
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Tuple, Union, Optional
from datetime import datetime

try:
    from flask import Flask, jsonify, request, Response  # type: ignore[import-untyped]
    from werkzeug.wrappers import Response as WerkzeugResponse  # type: ignore[import-untyped]
except ImportError:
    # Handle case where Flask is not available
    Flask = None  # type: ignore[misc]
    jsonify = None  # type: ignore[misc]
    request = None  # type: ignore[misc]
    Response = None  # type: ignore[misc]
    WerkzeugResponse = None  # type: ignore[misc]

from config import Config, get_settings
from handlers import (
    process_request, validate_input,
    EventHandler, MemoryEventStorage,
    EventFilterEngine, EventReplayEngine
)
from models import (
    AgentEvent, EventFilter, EventReplayRequest,
    EventStorageInfo, MemoryIntegrationStatus,
    EventType, EventPriority
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize event handling components
event_handler: Optional[EventHandler] = None
memory_storage: Optional[MemoryEventStorage] = None
filter_engine: Optional[EventFilterEngine] = None
replay_engine: Optional[EventReplayEngine] = None

# Create Flask app
if Flask is not None:
    app = Flask(__name__)
    app.config.from_object(Config)
else:
    app = None  # type: ignore[assignment]


async def initialize_event_system() -> None:
    """Initialize the event handling system with memory integration."""
    global event_handler, memory_storage, filter_engine, replay_engine

    try:
        settings = get_settings()
        logger.info("Initializing event system...")

        # Initialize memory storage
        memory_storage = MemoryEventStorage(
            memory_backend_url=settings.memory_backend_url,
            sqlite_db_path=settings.sqlite_db_path
        )
        await memory_storage.initialize()
        logger.info("✅ Memory storage initialized")

        # Initialize filter engine
        filter_engine = EventFilterEngine()
        logger.info("✅ Filter engine initialized")

        # Initialize replay engine
        replay_engine = EventReplayEngine(memory_storage)
        logger.info("✅ Replay engine initialized")

        # Initialize main event handler
        event_handler = EventHandler(memory_storage, filter_engine)
        await event_handler.initialize()
        logger.info("✅ Event handler initialized")

        logger.info("🎉 Event system fully initialized")

    except Exception as e:
        logger.error(f"❌ Failed to initialize event system: {e}")
        raise


def run_async_in_thread(coro):
    """Run async function in thread-safe way for Flask."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# ========== Health and Status Endpoints ==========

@app.route('/health', methods=['GET'])  # type: ignore[union-attr]
def health() -> Tuple[Any, int]:
    """Enhanced health check endpoint with memory system status."""
    try:
        health_info = {
            "status": "healthy",
            "service": "event-router",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Check memory system health if available
        if memory_storage:
            try:
                memory_status = run_async_in_thread(memory_storage.get_health_status())
                health_info["memory_system"] = json.dumps(memory_status)  # Convert to string
            except Exception as e:
                health_info["memory_system"] = json.dumps({"status": "error", "error": str(e)})  # Convert to string

        return jsonify(health_info), 200  # type: ignore[misc]

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500  # type: ignore[misc]


@app.route('/', methods=['GET'])  # type: ignore[union-attr]
def root() -> Tuple[Any, int]:
    """Root endpoint with service information."""
    return jsonify({  # type: ignore[misc]
        "service": "event-router",
        "description": "Agent lifecycle event routing and persistence service",
        "status": "running",
        "version": "1.0.0",
        "capabilities": [
            "event_storage",
            "event_filtering",
            "event_replay",
            "memory_integration",
            "agent_lifecycle_tracking"
        ],
        "endpoints": {
            "events": "/events",
            "replay": "/events/replay",
            "filter": "/events/filter",
            "storage": "/events/storage",
            "memory": "/memory/status"
        }
    }), 200


@app.route('/status', methods=['GET'])  # type: ignore[union-attr]
def status() -> Tuple[Any, int]:
    """Detailed status endpoint."""
    try:
        status_info = {
            "service": "event-router",
            "status": "operational",
            "version": "1.0.0",
            "uptime": datetime.utcnow().isoformat(),
            "components": {}
        }

        # Check component status
        if event_handler:
            status_info["components"]["event_handler"] = "operational"
        else:
            status_info["components"]["event_handler"] = "not_initialized"

        if memory_storage:
            try:
                storage_info = run_async_in_thread(memory_storage.get_storage_info())
                status_info["components"]["memory_storage"] = "operational"
                status_info["storage_stats"] = storage_info.dict()
            except Exception as e:
                status_info["components"]["memory_storage"] = f"error: {e}"
        else:
            status_info["components"]["memory_storage"] = "not_initialized"

        if filter_engine:
            status_info["components"]["filter_engine"] = "operational"
        else:
            status_info["components"]["filter_engine"] = "not_initialized"

        if replay_engine:
            status_info["components"]["replay_engine"] = "operational"
        else:
            status_info["components"]["replay_engine"] = "not_initialized"

        return jsonify(status_info), 200  # type: ignore[misc]

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]


# ========== Event Management Endpoints ==========

@app.route('/events', methods=['POST'])  # type: ignore[union-attr]
def create_event() -> Tuple[Any, int]:
    """Create and store a new agent event."""
    try:
        if not event_handler:
            return jsonify({"error": "Event system not initialized"}), 503  # type: ignore[misc]

        data: Dict[str, Any] = request.get_json() or {}  # type: ignore[union-attr]

        # Create event from data
        event = AgentEvent(**data)

        # Process and store event
        result = run_async_in_thread(event_handler.handle_event(event))

        return jsonify({  # type: ignore[misc]
            "success": True,
            "event_id": result["event_id"],
            "stored_in_memory": result["stored_in_memory"],
            "memory_id": result.get("memory_id"),
            "message": "Event created and stored successfully"
        }), 201

    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]


@app.route('/events', methods=['GET'])  # type: ignore[union-attr]
def list_events() -> Tuple[Any, int]:
    """List events with optional filtering."""
    try:
        if not memory_storage:
            return jsonify({"error": "Memory storage not initialized"}), 503  # type: ignore[misc]

        # Parse query parameters
        params = dict(request.args)  # type: ignore[union-attr]

        # Create filter from params
        event_filter = EventFilter(
            event_types=[EventType(t) for t in params.get('event_types', '').split(',') if t] or None,
            agent_ids=params.get('agent_ids', '').split(',') if params.get('agent_ids') else None,
            task_ids=params.get('task_ids', '').split(',') if params.get('task_ids') else None,
            project_ids=params.get('project_ids', '').split(',') if params.get('project_ids') else None,
            priority=EventPriority(params.get('priority')) if params.get('priority') else None,
            tags=params.get('tags', '').split(',') if params.get('tags') else None,
            start_time=None,  # Could parse from params if needed
            end_time=None,  # Could parse from params if needed
            limit=int(params.get('limit', 100)),
            offset=int(params.get('offset', 0))
        )

        # Get filtered events
        events = run_async_in_thread(memory_storage.get_events(event_filter))

        return jsonify({  # type: ignore[misc]
            "events": [event.dict() for event in events],
            "count": len(events),
            "filter": event_filter.dict(exclude_none=True)
        }), 200

    except Exception as e:
        logger.error(f"Error listing events: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]


@app.route('/events/filter', methods=['POST'])  # type: ignore[union-attr]
def filter_events() -> Tuple[Any, int]:
    """Filter events using complex criteria."""
    try:
        if not filter_engine or not memory_storage:
            return jsonify({"error": "Event system not initialized"}), 503  # type: ignore[misc]

        data: Dict[str, Any] = request.get_json() or {}  # type: ignore[union-attr]

        # Create filter from request
        event_filter = EventFilter(**data)

        # Apply filtering
        events = run_async_in_thread(filter_engine.filter_events(memory_storage, event_filter))

        return jsonify({  # type: ignore[misc]
            "events": [event.dict() for event in events],
            "count": len(events),
            "filter_applied": event_filter.dict(exclude_none=True)
        }), 200

    except Exception as e:
        logger.error(f"Error filtering events: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]


@app.route('/events/replay', methods=['POST'])  # type: ignore[union-attr]
def replay_events() -> Tuple[Any, int]:
    """Replay events for crash recovery."""
    try:
        if not replay_engine:
            return jsonify({"error": "Replay engine not initialized"}), 503  # type: ignore[misc]

        data: Dict[str, Any] = request.get_json() or {}  # type: ignore[union-attr]

        # Create replay request
        replay_request = EventReplayRequest(**data)

        # Execute replay
        replay_result = run_async_in_thread(replay_engine.replay_events(replay_request))

        return jsonify({  # type: ignore[misc]
            "success": True,
            "replayed_events": replay_result["event_count"],
            "session_id": replay_request.session_id,
            "replay_summary": replay_result["summary"],
            "message": "Events replayed successfully"
        }), 200

    except Exception as e:
        logger.error(f"Error replaying events: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]


@app.route('/events/storage', methods=['GET'])  # type: ignore[union-attr]
def storage_info() -> Tuple[Any, int]:
    """Get event storage information."""
    try:
        if not memory_storage:
            return jsonify({"error": "Memory storage not initialized"}), 503  # type: ignore[misc]

        storage_info = run_async_in_thread(memory_storage.get_storage_info())

        return jsonify(storage_info.dict()), 200  # type: ignore[misc]

    except Exception as e:
        logger.error(f"Error getting storage info: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]


@app.route('/memory/status', methods=['GET'])  # type: ignore[union-attr]
def memory_status() -> Tuple[Any, int]:
    """Get memory system integration status."""
    try:
        if not memory_storage:
            return jsonify({"error": "Memory storage not initialized"}), 503  # type: ignore[misc]

        status = run_async_in_thread(memory_storage.get_integration_status())

        return jsonify(status.dict()), 200  # type: ignore[misc]

    except Exception as e:
        logger.error(f"Error getting memory status: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]


# ========== Legacy Compatibility Endpoint ==========

@app.route('/process', methods=['POST'])  # type: ignore[union-attr]
def process() -> Tuple[Any, int]:
    """Legacy process endpoint - redirects to event creation."""
    try:
        data: Dict[str, Any] = request.get_json() or {}  # type: ignore[union-attr]

        # Validate input
        is_valid, error = validate_input(data)
        if not is_valid:
            return jsonify({"error": error}), 400  # type: ignore[misc]

        # Process request using legacy handler for backward compatibility
        result = process_request(data)

        return jsonify({  # type: ignore[misc]
            "success": True,
            "data": result,
            "message": "Request processed successfully (legacy mode)"
        }), 200
    except Exception as e:
        logger.error(f"Error processing legacy request: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]

if __name__ == "__main__":
    if app is not None:
        # Initialize event system before starting server
        try:
            print("🚀 Starting Event Router Service...")
            run_async_in_thread(initialize_event_system())
            print("✅ Event system initialized successfully")

            settings = get_settings()
            print(f"🌐 Starting server on {settings.host}:{settings.port}")
            app.run(host=settings.host, port=settings.port, debug=settings.debug)

        except Exception as e:
            logger.error(f"❌ Failed to start service: {e}")
            print(f"❌ Failed to start service: {e}")
            exit(1)
    else:
        print("Flask not available, cannot start server")
        exit(1)
