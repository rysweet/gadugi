from memory_utils.agent_interface import AgentMemoryInterface
agent = AgentMemoryInterface("pm-001", "program-manager")

# Get project context and priorities
context = agent.get_project_context()
priorities = agent.read_memory("project", "priorities")
