#!/usr/bin/env python3
"""
Start the Enhanced MCP Service with Neo4j backend.
This replaces the SQLite-based simple_mcp_service with full Neo4j support.
"""

import os
import sys
import asyncio
from pathlib import Path

# Set environment variables for Neo4j connection
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7689")
os.environ.setdefault("NEO4J_USERNAME", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "gadugi-password")
os.environ.setdefault("NEO4J_DATABASE", "neo4j")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


async def main():
    """Start the enhanced MCP service."""
    print("=" * 60)
    print("🚀 Starting Enhanced MCP Service with Neo4j Backend")
    print("=" * 60)
    print(f"Neo4j URI: {os.environ['NEO4J_URI']}")
    print(f"Neo4j Database: {os.environ['NEO4J_DATABASE']}")
    print("=" * 60)

    # Import and run the enhanced service
    from enhanced_mcp_service import app
    import uvicorn

    # Run the server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Service stopped gracefully")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
