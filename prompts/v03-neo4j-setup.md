# Setup Neo4j for Gadugi v0.3

## Task Description
Initialize and verify Neo4j database for Gadugi v0.3 implementation.

## Requirements
1. Initialize Neo4j schema using the cypher script at neo4j/init/init_schema.cypher
2. Verify Neo4j is running on port 7475 (custom port for Gadugi)
3. Test connection using the test script at neo4j/test_connection.py
4. Create comprehensive integration tests

## Technical Details
- Neo4j container name: gadugi-neo4j
- Port: 7475 (HTTP), 7689 (Bolt)
- Auth: neo4j/gadugi-password
- Schema file: neo4j/init/init_schema.cypher

## Execution Requirements
- Use `uv run` for all Python commands (UV project)
- Run pyright checks on any Python code
- Ensure all tests pass before completing

/agent:workflow-manager

Execute complete workflow for Neo4j setup task