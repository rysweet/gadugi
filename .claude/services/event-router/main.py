"""
event-router Service - Flask Implementation
Generated from recipe: event-router
"""

import logging
from typing import Any, Dict, Tuple, Union

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

from .config import Config
from .handlers import process_request, validate_input

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
if Flask is not None:
    app = Flask(__name__)
    app.config.from_object(Config)
else:
    app = None  # type: ignore[assignment]

@app.route('/health', methods=['GET'])  # type: ignore[union-attr]
def health() -> Tuple[Any, int]:
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200  # type: ignore[misc]

@app.route('/', methods=['GET'])  # type: ignore[union-attr]
def root() -> Tuple[Any, int]:
    """Root endpoint."""
    return jsonify({  # type: ignore[misc]
        "service": "event-router",
        "status": "running",
        "version": "0.1.0"
    }), 200

@app.route('/status', methods=['GET'])  # type: ignore[union-attr]
def status() -> Tuple[Any, int]:
    """Status endpoint."""
    return jsonify({  # type: ignore[misc]
        "service": "event-router",
        "status": "operational",
        "version": "0.1.0"
    }), 200

@app.route('/process', methods=['POST'])  # type: ignore[union-attr]
def process() -> Tuple[Any, int]:
    """Process incoming request."""
    try:
        data: Dict[str, Any] = request.get_json() or {}  # type: ignore[union-attr]

        # Validate input
        is_valid, error = validate_input(data)
        if not is_valid:
            return jsonify({"error": error}), 400  # type: ignore[misc]

        # Process request
        result = process_request(data)

        return jsonify({  # type: ignore[misc]
            "success": True,
            "data": result,
            "message": "Request processed successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[misc]

if __name__ == "__main__":
    if app is not None:
        app.run(host="0.0.0.0", port=8000, debug=False)
    else:
        print("Flask not available, cannot start server")