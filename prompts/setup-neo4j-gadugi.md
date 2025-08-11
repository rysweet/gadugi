# Setup Neo4j for Gadugi

## Objective
Initialize and test Neo4j database integration for Gadugi v0.3

## Requirements
1. Initialize Neo4j schema using the cypher script at neo4j/init/init_schema.cypher
2. Test Neo4j connection and verify it's working on port 7475
3. Create integration test for Neo4j connectivity

## Technical Details
- Neo4j is configured to run on port 7475 (non-standard port)
- Schema initialization script exists at neo4j/init/init_schema.cypher
- Must ensure proper connection testing and error handling

## Testing Requirements
- Create integration test that verifies:
  - Neo4j service is accessible on port 7475
  - Schema is properly initialized
  - Basic CRUD operations work
- Use `uv run pytest` for test execution

## Success Criteria
- Neo4j schema successfully initialized
- Connection test passes on port 7475
- Integration test suite created and passing
