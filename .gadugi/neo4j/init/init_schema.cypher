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
MERGE (system:Agent {id: 'system'})
ON CREATE SET system.name = 'Gadugi System', system.type = 'system', system.created = datetime();
MERGE (orchestrator:Agent {id: 'orchestrator'})
ON CREATE SET orchestrator.name = 'Orchestrator Agent', orchestrator.type = 'orchestrator', orchestrator.created = datetime();
MERGE (workflow_manager:Agent {id: 'workflow_manager'})
ON CREATE SET workflow_manager.name = 'Workflow Manager', workflow_manager.type = 'manager', workflow_manager.created = datetime();

// Create tool nodes
MERGE (read_tool:Tool {id: 'read'})
ON CREATE SET read_tool.name = 'Read', read_tool.category = 'file_ops', read_tool.created = datetime();
MERGE (write_tool:Tool {id: 'write'})
ON CREATE SET write_tool.name = 'Write', write_tool.category = 'file_ops', write_tool.created = datetime();
MERGE (bash_tool:Tool {id: 'bash'})
ON CREATE SET bash_tool.name = 'Bash', bash_tool.category = 'execution', bash_tool.created = datetime();
MERGE (grep_tool:Tool {id: 'grep'})
ON CREATE SET grep_tool.name = 'Grep', grep_tool.category = 'search', grep_tool.created = datetime();

// Create relationships between system agents
MATCH (system:Agent {id: 'system'})
MATCH (orchestrator:Agent {id: 'orchestrator'})
MATCH (workflow_manager:Agent {id: 'workflow_manager'})
MERGE (system)-[:MANAGES]->(orchestrator)
MERGE (orchestrator)-[:COORDINATES]->(workflow_manager);

// Create agent-tool relationships
MATCH (orchestrator:Agent {id: 'orchestrator'})
MATCH (workflow_manager:Agent {id: 'workflow_manager'})
MATCH (read_tool:Tool {id: 'read'})
MATCH (write_tool:Tool {id: 'write'})
MATCH (bash_tool:Tool {id: 'bash'})
MERGE (orchestrator)-[:USES]->(read_tool)
MERGE (orchestrator)-[:USES]->(write_tool)
MERGE (orchestrator)-[:USES]->(bash_tool)
MERGE (workflow_manager)-[:USES]->(bash_tool);

// Return confirmation
RETURN "Schema initialized successfully" as message;
