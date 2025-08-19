"""
event-router Service - Flask Implementation
Generated from recipe: event-router
"""

import logging
from flask import Flask, jsonify, request

from .config import Config
from .handlers import process_request, validate_input

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({
        "service": "event-router",
        "status": "running",
        "version": "0.1.0"
    }), 200

@app.route('/status', methods=['GET'])
def status():
    """Status endpoint."""
    return jsonify({
        "service": "event-router",
        "status": "operational",
        "version": "0.1.0"
    }), 200

@app.route('/process', methods=['POST'])
def process():
    """Process incoming request."""
    try:
        data = request.get_json()

        # Validate input
        is_valid, error = validate_input(data)
        if not is_valid:
            return jsonify({"error": error}), 400

        # Process request
        result = process_request(data)

        return jsonify({
            "success": True,
            "data": result,
            "message": "Request processed successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
