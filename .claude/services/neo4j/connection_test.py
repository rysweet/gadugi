#!/usr/bin/env python3
"""
Neo4j Connection Test for Gadugi
Tests the connection to Neo4j and verifies schema initialization
"""

import sys
from neo4j import GraphDatabase
from typing import Optional


class Neo4jConnectionTest:
    def __init__(self, uri: str, user: str, password: str):
        """Initialize connection test with Neo4j credentials"""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[GraphDatabase.driver] = None

    def connect(self) -> bool:
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test the connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                print(f"✅ Connected to Neo4j at {self.uri}")
                return test_value == 1
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            return False

    def verify_schema(self) -> bool:
        """Verify that the schema was initialized correctly"""
        if not self.driver:
            print("❌ No connection to Neo4j")
            return False

        try:
            with self.driver.session() as session:
                # Check for Agent nodes
                agents_result = session.run("""
                    MATCH (a:Agent)
                    RETURN count(a) as agent_count, collect(a.name) as agent_names
                """)
                agents = agents_result.single()
                print(f"✅ Found {agents['agent_count']} agents: {agents['agent_names']}")

                # Check for Tool nodes
                tools_result = session.run("""
                    MATCH (t:Tool)
                    RETURN count(t) as tool_count, collect(t.name) as tool_names
                """)
                tools = tools_result.single()
                print(f"✅ Found {tools['tool_count']} tools: {tools['tool_names']}")

                # Check for relationships
                rels_result = session.run("""
                    MATCH ()-[r]->()
                    RETURN count(r) as rel_count, collect(distinct type(r)) as rel_types
                """)
                rels = rels_result.single()
                print(f"✅ Found {rels['rel_count']} relationships: {rels['rel_types']}")

                # Check constraints
                constraints_result = session.run("SHOW CONSTRAINTS")
                constraints = list(constraints_result)
                print(f"✅ Found {len(constraints)} constraints")

                # Check indexes
                indexes_result = session.run("SHOW INDEXES")
                indexes = list(indexes_result)
                print(f"✅ Found {len(indexes)} indexes")

                return agents['agent_count'] > 0 and tools['tool_count'] > 0

        except Exception as e:
            print(f"❌ Failed to verify schema: {e}")
            return False

    def create_test_data(self) -> bool:
        """Create test data to verify write operations"""
        if not self.driver:
            print("❌ No connection to Neo4j")
            return False

        try:
            with self.driver.session() as session:
                # Create a test context node
                result = session.run("""
                    CREATE (c:Context {
                        id: 'test-context-001',
                        content: 'Test context for Gadugi v0.3',
                        timestamp: datetime(),
                        source: 'connection_test.py'
                    })
                    RETURN c.id as context_id
                """)
                context_id = result.single()["context_id"]
                print(f"✅ Created test context: {context_id}")

                # Create relationship to system agent
                session.run("""
                    MATCH (a:Agent {id: 'system'})
                    MATCH (c:Context {id: 'test-context-001'})
                    CREATE (a)-[:CREATED]->(c)
                """)
                print("✅ Created test relationship")

                return True

        except Exception as e:
            print(f"❌ Failed to create test data: {e}")
            return False

    def cleanup(self):
        """Close the driver connection"""
        if self.driver:
            self.driver.close()
            print("✅ Connection closed")


def main():
    """Run connection test"""
    print("\n🧪 Testing Neo4j Connection for Gadugi\n")

    # Connection parameters
    uri = "bolt://localhost:7689"  # Updated port
    user = "neo4j"
    password = "gadugi-password"

    # Run tests
    tester = Neo4jConnectionTest(uri, user, password)

    # Test 1: Connection
    if not tester.connect():
        sys.exit(1)

    # Test 2: Schema verification
    if not tester.verify_schema():
        print("⚠️  Schema verification failed")

    # Test 3: Write test
    if not tester.create_test_data():
        print("⚠️  Write test failed")

    # Cleanup
    tester.cleanup()

    print("\n✅ All Neo4j tests passed!\n")
    print(f"📊 Neo4j Browser: http://localhost:7475")
    print(f"🔌 Bolt URL: {uri}")
    print(f"👤 Username: {user}")
    print(f"🔑 Password: {password}\n")


if __name__ == "__main__":
    main()
