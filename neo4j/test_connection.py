#!/usr/bin/env python3
"""
Test Neo4j connection and initialization for Gadugi.
"""

import sys
import os
from datetime import datetime

from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable, AuthError
from typing import List


class Neo4jConnection:
    """Manages Neo4j database connection."""

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
    ):
        # Use environment variables with fallbacks
        neo4j_host = os.getenv('NEO4J_HOST', 'localhost')
        neo4j_port = os.getenv('NEO4J_BOLT_PORT', '7687')
        self.uri = uri or f"bolt://{neo4j_host}:{neo4j_port}"
        self.user = user or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'changeme')
        self.driver = None

    def connect(self) -> bool:
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=basic_auth(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            print(f"✅ Connected to Neo4j at {self.uri}")
            return True
        except ServiceUnavailable:
            print(f"❌ Neo4j is not available at {self.uri}")
            print(
                "   Please ensure Neo4j is running: docker-compose -f docker-compose.gadugi.yml up -d neo4j"
            )
            return False
        except AuthError:
            print(f"❌ Authentication failed for user {self.user}")
            print("   Check your credentials in docker-compose.gadugi.yml")
            return False
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()

    def test_schema(self) -> bool:
        """Test that schema is properly initialized."""
        if not self.driver:
            print("❌ Not connected to database")
            return False

        try:
            with self.driver.session() as session:
                # Check for system agent
                result = session.run(
                    "MATCH (a:Agent {id: 'system'}) RETURN a.name AS name"
                )
                record = result.single()
                if record:
                    print(f"✅ System agent found: {record['name']}")
                else:
                    print("❌ System agent not found - schema may not be initialized")
                    return False

                # Check for root memory
                result = session.run(
                    "MATCH (m:Memory {id: 'root'}) RETURN m.type AS type"
                )
                record = result.single()
                if record:
                    print(f"✅ Root memory found: {record['type']}")
                else:
                    print("❌ Root memory not found")
                    return False

                # Count constraints
                result = session.run(
                    "SHOW CONSTRAINTS YIELD name RETURN count(*) AS count"
                )
                count = result.single()["count"]
                print(f"✅ Found {count} constraints")

                # Count indexes
                result = session.run(
                    "SHOW INDEXES YIELD name WHERE name <> 'constraint' RETURN count(*) AS count"
                )
                count = result.single()["count"]
                print(f"✅ Found {count} indexes")

                return True

        except Exception as e:
            print(f"❌ Schema test failed: {e}")
            return False

    def create_test_memory(self) -> bool:
        """Create a test memory node."""
        if not self.driver:
            return False

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    CREATE (m:Memory {
                        id: $id,
                        type: 'test',
                        content: $content,
                        timestamp: datetime(),
                        namespace: 'test'
                    })
                    RETURN m.id AS id
                    """,
                    id=f"test-memory-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    content="This is a test memory created by the connection test script",
                )

                memory_id = result.single()["id"]
                print(f"✅ Created test memory: {memory_id}")
                return True

        except Exception as e:
            print(f"❌ Failed to create test memory: {e}")
            return False

    def list_recent_memories(self, limit: int = 5) -> List[Dict]:
        """List recent memories from the database."""
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (m:Memory)
                    WHERE m.id <> 'root'
                    RETURN m.id AS id, m.type AS type, m.content AS content, m.timestamp AS timestamp
                    ORDER BY m.timestamp DESC
                    LIMIT $limit
                    """,
                    limit=limit,
                )

                memories = []
                for record in result:
                    memories.append(
                        {
                            "id": record["id"],
                            "type": record["type"],
                            "content": record["content"],
                            "timestamp": record["timestamp"],
                        }
                    )

                if memories:
                    print(f"\n📚 Recent memories ({len(memories)} found):")
                    for mem in memories:
                        print(f"  - {mem['id']}: {mem['content'][:50]}...")
                else:
                    print("\n📚 No memories found (besides root)")

                return memories

        except Exception as e:
            print(f"❌ Failed to list memories: {e}")
            return []

    def get_statistics(self) -> Dict:
        """Get database statistics."""
        if not self.driver:
            return {}

        try:
            with self.driver.session() as session:
                # Count nodes by label
                result = session.run(
                    """
                    CALL db.labels() YIELD label
                    CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {})
                    YIELD value
                    RETURN label, value.count AS count
                    ORDER BY label
                    """
                )

                stats = {"nodes": {}}
                for record in result:
                    stats["nodes"][record["label"]] = record["count"]

                # Count relationships
                result = session.run(
                    """
                    MATCH ()-[r]->()
                    RETURN type(r) AS type, count(r) AS count
                    ORDER BY count DESC
                    """
                )

                stats["relationships"] = {}
                for record in result:
                    stats["relationships"][record["type"]] = record["count"]

                print("\n📊 Database Statistics:")
                print("  Nodes:")
                for label, count in stats["nodes"].items():
                    print(f"    - {label}: {count}")
                print("  Relationships:")
                for rel_type, count in stats["relationships"].items():
                    print(f"    - {rel_type}: {count}")

                return stats

        except Exception as e:
            # APOC might not be installed
            print(f"⚠️  Could not get full statistics (APOC may not be installed): {e}")

            # Try basic statistics
            try:
                with self.driver.session() as session:
                    result = session.run("MATCH (n) RETURN count(n) AS nodes")
                    node_count = result.single()["nodes"]

                    result = session.run(
                        "MATCH ()-[r]->() RETURN count(r) AS relationships"
                    )
                    rel_count = result.single()["relationships"]

                    print("\n📊 Basic Statistics:")
                    print(f"  Total nodes: {node_count}")
                    print(f"  Total relationships: {rel_count}")

                    return {"total_nodes": node_count, "total_relationships": rel_count}
            except:
                return {}


def main():
    """Main test function."""
    print("🚀 Testing Neo4j Connection for Gadugi\n")

    # Create connection
    conn = Neo4jConnection()

    # Test connection
    if not conn.connect():
        print("\n⚠️  Please start Neo4j first:")
        print("  docker-compose -f docker-compose.gadugi.yml up -d neo4j")
        return 1

    # Test schema
    print("\n🔍 Testing Schema...")
    if not conn.test_schema():
        print("\n⚠️  Schema not initialized. Run the init script:")
        print(
            "  docker exec gadugi-neo4j cypher-shell -u neo4j -p gadugi-password < neo4j/init/init_schema.cypher"
        )

    # Create test memory
    print("\n✏️  Creating Test Data...")
    conn.create_test_memory()

    # List memories
    conn.list_recent_memories()

    # Get statistics
    conn.get_statistics()

    # Close connection
    conn.close()

    print("\n✅ Neo4j connection test completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
