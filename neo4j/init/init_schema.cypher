// Gadugi Neo4j Schema Initialization
// This file creates the basic schema for the Gadugi knowledge graph

// Create constraints for unique IDs
CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT tool_id_unique IF NOT EXISTS FOR (t:Tool) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT context_id_unique IF NOT EXISTS FOR (c:Context) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT workflow_id_unique IF NOT EXISTS FOR (w:Workflow) REQUIRE w.id IS UNIQUE;

// Create indexes for better query performance
CREATE INDEX agent_name_index IF NOT EXISTS FOR (a:Agent) ON (a.name);
CREATE INDEX tool_name_index IF NOT EXISTS FOR (t:Tool) ON (t.name);
CREATE INDEX context_timestamp_index IF NOT EXISTS FOR (c:Context) ON (c.timestamp);
CREATE INDEX workflow_status_index IF NOT EXISTS FOR (w:Workflow) ON (w.status);

// Create initial nodes
MERGE (system:Agent {id: 'system', name: 'Gadugi System', type: 'system', created: datetime()})
MERGE (orchestrator:Agent {id: 'orchestrator', name: 'Orchestrator Agent', type: 'orchestrator', created: datetime()})
MERGE (workflow_manager:Agent {id: 'workflow_manager', name: 'Workflow Manager', type: 'manager', created: datetime()})

// Create relationships between system agents
MERGE (system)-[:MANAGES]->(orchestrator)
MERGE (orchestrator)-[:COORDINATES]->(workflow_manager)

// Create tool nodes
MERGE (read_tool:Tool {id: 'read', name: 'Read', category: 'file_ops', created: datetime()})
MERGE (write_tool:Tool {id: 'write', name: 'Write', category: 'file_ops', created: datetime()})
MERGE (bash_tool:Tool {id: 'bash', name: 'Bash', category: 'execution', created: datetime()})
MERGE (grep_tool:Tool {id: 'grep', name: 'Grep', category: 'search', created: datetime()})

// Create agent-tool relationships
MERGE (orchestrator)-[:USES]->(read_tool)
MERGE (orchestrator)-[:USES]->(write_tool)
MERGE (orchestrator)-[:USES]->(bash_tool)
MERGE (workflow_manager)-[:USES]->(bash_tool)

// Return confirmation
<<<<<<< HEAD
RETURN "Schema initialized successfully" as message;
=======
RETURN "Schema initialized successfully" as message;
>>>>>>> feature/gadugi-v0.3-regeneration
