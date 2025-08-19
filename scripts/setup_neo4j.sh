#!/bin/bash
# Setup Neo4j for Gadugi v0.3

set -e

echo "🚀 Setting up Neo4j for Gadugi..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Neo4j container
echo "📦 Starting Neo4j container..."
docker-compose -f docker-compose.gadugi.yml up -d neo4j

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker exec gadugi-neo4j cypher-shell -u neo4j -p gadugi-password "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi

    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Neo4j failed to start after $max_attempts attempts"
    exit 1
fi

# Initialize schema
echo "📝 Initializing schema..."
docker exec gadugi-neo4j cypher-shell -u neo4j -p gadugi-password < neo4j/init/init_schema.cypher

# Test connection
echo "🧪 Testing connection..."
if command -v python3 &> /dev/null; then
    python3 neo4j/test_connection.py
else
    echo "⚠️  Python not found, skipping connection test"
fi

echo ""
echo "✅ Neo4j setup complete!"
echo ""
echo "📊 Neo4j Browser: http://localhost:7475"
echo "🔌 Bolt URL: bolt://localhost:7688"
echo "👤 Username: neo4j"
echo "🔑 Password: gadugi-password"
echo ""
echo "To stop Neo4j: docker-compose -f docker-compose.gadugi.yml down"
echo "To view logs: docker logs -f gadugi-neo4j"
