// Neo4j Schema for Gadugi v0.3
// This file defines the graph schema including nodes, relationships, and constraints

// ============================================
// NODE CONSTRAINTS AND INDEXES
// ============================================

// Agent Node
CREATE CONSTRAINT agent_id IF NOT EXISTS
FOR (a:Agent) REQUIRE a.id IS UNIQUE;

CREATE INDEX agent_type IF NOT EXISTS
FOR (a:Agent) ON (a.type);

CREATE INDEX agent_status IF NOT EXISTS
FOR (a:Agent) ON (a.status);

// Memory Node
CREATE CONSTRAINT memory_id IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE;

CREATE INDEX memory_agent IF NOT EXISTS
FOR (m:Memory) ON (m.agent_id);

CREATE INDEX memory_type IF NOT EXISTS
FOR (m:Memory) ON (m.type);

CREATE INDEX memory_timestamp IF NOT EXISTS
FOR (m:Memory) ON (m.timestamp);

// Knowledge Node
CREATE CONSTRAINT knowledge_id IF NOT EXISTS
FOR (k:Knowledge) REQUIRE k.id IS UNIQUE;

CREATE INDEX knowledge_domain IF NOT EXISTS
FOR (k:Knowledge) ON (k.domain);

CREATE INDEX knowledge_confidence IF NOT EXISTS
FOR (k:Knowledge) ON (k.confidence);

// Task Node
CREATE CONSTRAINT task_id IF NOT EXISTS
FOR (t:Task) REQUIRE t.id IS UNIQUE;

CREATE INDEX task_status IF NOT EXISTS
FOR (t:Task) ON (t.status);

CREATE INDEX task_priority IF NOT EXISTS
FOR (t:Task) ON (t.priority);

CREATE INDEX task_agent IF NOT EXISTS
FOR (t:Task) ON (t.assigned_to);

// User Node
CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE INDEX user_role IF NOT EXISTS
FOR (u:User) ON (u.role);

// Context Node
CREATE CONSTRAINT context_id IF NOT EXISTS
FOR (c:Context) REQUIRE c.id IS UNIQUE;

CREATE INDEX context_agent IF NOT EXISTS
FOR (c:Context) ON (c.agent_id);

// Team Node
CREATE CONSTRAINT team_id IF NOT EXISTS
FOR (tm:Team) REQUIRE tm.id IS UNIQUE;

// Workflow Node
CREATE CONSTRAINT workflow_id IF NOT EXISTS
FOR (w:Workflow) REQUIRE w.id IS UNIQUE;

CREATE INDEX workflow_status IF NOT EXISTS
FOR (w:Workflow) ON (w.status);

// ============================================
// NODE PROPERTIES DOCUMENTATION
// ============================================

// Agent Node Properties:
// - id: string (unique identifier)
// - name: string (human-readable name)
// - type: string (agent type: worker, coordinator, specialist, monitor)
// - version: string (agent version)
// - status: string (initializing, running, paused, stopped, error)
// - created_at: datetime
// - updated_at: datetime
// - capabilities: string[] (list of capabilities)
// - metadata: string (JSON encoded metadata)

// Memory Node Properties:
// - id: string (unique identifier)
// - agent_id: string (owner agent)
// - content: string (memory content)
// - type: string (episodic, semantic, procedural, working)
// - timestamp: datetime
// - priority: string (low, normal, high, critical)
// - importance: float (0.0 to 1.0)
// - tags: string[] (categorization tags)
// - access_count: int
// - decay_rate: float

// Knowledge Node Properties:
// - id: string (unique identifier)
// - title: string
// - content: string
// - domain: string (knowledge domain)
// - confidence: float (0.0 to 1.0)
// - source: string
// - created_at: datetime
// - verified: boolean
// - version: int

// Task Node Properties:
// - id: string (unique identifier)
// - name: string
// - description: string
// - type: string (task type)
// - status: string (pending, scheduled, running, completed, failed, cancelled)
// - priority: string (low, normal, high, critical)
// - created_at: datetime
// - started_at: datetime
// - completed_at: datetime
// - assigned_to: string (agent id)
// - result: string (JSON encoded result)
// - timeout_seconds: int

// User Node Properties:
// - id: string (unique identifier)
// - name: string
// - email: string
// - role: string (admin, developer, observer)
// - created_at: datetime
// - preferences: string (JSON encoded preferences)

// Context Node Properties:
// - id: string (unique identifier)
// - agent_id: string
// - task_id: string
// - state: string (JSON encoded state)
// - created_at: datetime
// - updated_at: datetime

// Team Node Properties:
// - id: string (unique identifier)
// - name: string
// - created_at: datetime
// - objectives: string (JSON encoded objectives)
// - performance_score: float

// Workflow Node Properties:
// - id: string (unique identifier)
// - name: string
// - description: string
// - status: string (draft, scheduled, running, completed, failed)
// - created_at: datetime
// - started_at: datetime
// - completed_at: datetime
// - config: string (JSON encoded configuration)

// ============================================
// RELATIONSHIP TYPES
// ============================================

// Agent Relationships
// (a1:Agent)-[:DELEGATES_TO]->(a2:Agent)
// (a:Agent)-[:CREATES]->(m:Memory)
// (a:Agent)-[:EXECUTES]->(t:Task)
// (a:Agent)-[:KNOWS]->(k:Knowledge)
// (a:Agent)-[:MEMBER_OF]->(tm:Team)
// (a:Agent)-[:USES_CONTEXT]->(c:Context)

// Memory Relationships
// (m1:Memory)-[:REFERENCES]->(m2:Memory)
// (m:Memory)-[:ABOUT]->(k:Knowledge)
// (m:Memory)-[:GENERATED_BY]->(t:Task)
// (m:Memory)-[:ASSOCIATES_WITH {strength: float}]->(m2:Memory)

// Task Relationships
// (t1:Task)-[:DEPENDS_ON]->(t2:Task)
// (t1:Task)-[:SUBTASK_OF]->(t2:Task)
// (t:Task)-[:ASSIGNED_TO]->(a:Agent)
// (t:Task)-[:REQUESTED_BY]->(u:User)
// (t:Task)-[:PART_OF]->(w:Workflow)
// (t:Task)-[:PRODUCES]->(k:Knowledge)

// Knowledge Relationships
// (k1:Knowledge)-[:RELATED_TO {similarity: float}]->(k2:Knowledge)
// (k:Knowledge)-[:DERIVED_FROM]->(m:Memory)
// (k:Knowledge)-[:VERIFIED_BY]->(a:Agent)
// (k:Knowledge)-[:USED_BY]->(t:Task)

// Context Relationships
// (c:Context)-[:INCLUDES]->(m:Memory)
// (c1:Context)-[:INHERITS_FROM]->(c2:Context)
// (c:Context)-[:FOR_TASK]->(t:Task)

// Team Relationships
// (tm:Team)-[:HAS_LEADER]->(a:Agent)
// (tm:Team)-[:WORKS_ON]->(w:Workflow)
// (tm1:Team)-[:COLLABORATES_WITH]->(tm2:Team)

// Workflow Relationships
// (w:Workflow)-[:CONTAINS]->(t:Task)
// (w:Workflow)-[:MANAGED_BY]->(a:Agent)
// (w:Workflow)-[:CREATED_BY]->(u:User)
// (w1:Workflow)-[:TRIGGERS]->(w2:Workflow)

// User Relationships
// (u:User)-[:OWNS]->(a:Agent)
// (u:User)-[:APPROVES]->(t:Task)
// (u:User)-[:MEMBER_OF]->(tm:Team)
