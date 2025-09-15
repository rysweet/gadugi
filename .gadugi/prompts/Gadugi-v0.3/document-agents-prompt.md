# Gadugi Agent Documentation and Refactoring Prompt

## Overview

This prompt guides the comprehensive documentation and refactoring of all agents in the Gadugi multi-agent development orchestration system. The goal is to create a clean, modular agent architecture following the "bricks & studs" philosophy while ensuring proper documentation for both human and AI consumption.

## Problem Statement

The current agent system in Gadugi has evolved organically, resulting in:
- Mixed documentation styles across agents
- Embedded Python code within markdown agent files
- Inconsistent interface definitions
- Lack of clear modular boundaries
- Difficulty for AI agents to understand and work with existing agents

This creates challenges for:
- Maintaining and updating agents
- Creating new agents following consistent patterns
- AI agents understanding existing capabilities
- Ensuring proper separation of concerns

## Feature Requirements

### Functional Requirements

1. **Agent Discovery and Analysis**
   - Scan all agents in `.claude/agents/` directory
   - Identify agents with embedded Python code
   - Analyze agent interfaces, roles, and dependencies
   - Map agent hierarchies and relationships

2. **Modular Agent Structure Creation**
   - Create organized folder structure at `/prompts/Gadugi-v0.3/agents/`
   - Each agent gets its own directory following CamelCase naming
   - Extract embedded Python code to separate `src/` files within agent directories
   - Create clean markdown documentation following Claude Code sub-agent format

3. **Documentation Standards**
   - Follow Claude Code sub-agent specification (https://docs.anthropic.com/en/docs/claude-code/sub-agents)
   - Include required fields: Role, Requirements, Function, Job Description, Tools
   - Create clear contracts and interfaces for each agent
   - Document input/output specifications and dependencies

4. **Code Extraction and Organization**
   - Extract all embedded Python code to dedicated `.py` files
   - Organize extracted code in `src/` subdirectories within each agent folder
   - Update agent documentation to reference extracted code as tools
   - Maintain functionality while improving modularity

5. **Comprehensive Agent Registry**
   - Generate master `agents.md` file listing all agents
   - Include agent summaries, capabilities, and relationships
   - Create hierarchical organization showing agent coordination patterns
   - Document usage patterns and best practices

### Technical Requirements

- Follow the "bricks & studs" modular design philosophy from Guidelines.md
- Maintain architectural integrity with minimal implementation
- Use ruthless simplicity while preserving functionality
- Ensure each agent directory is self-contained with clear contracts
- Create documentation that supports AI agent comprehension and generation

### Integration Requirements

- Preserve existing agent functionality and interfaces
- Maintain compatibility with current orchestration patterns
- Document integration points with shared modules
- Ensure agent hierarchy (orchestrator → WorkflowManager → specialized agents) is clear

## Technical Analysis

### Current Architecture Review

The existing `.claude/agents/` directory contains:
- **25+ agent files** with varying documentation quality
- **Mixed formats**: Some with embedded Python, others pure markdown
- **Complex agents**: TeamCoach, SystemDesignReviewer, PRBacklogManager with substantial codebases
- **Hierarchical structure**: Clear orchestration patterns with OrchestratorAgent at the top

### Proposed Technical Approach

1. **"Brick" Definition for Agents**
   - Each agent becomes a self-contained "brick" with clear "stud" interfaces
   - Agent directory structure:
     ```
     /prompts/Gadugi-v0.3/agents/AgentName/
     ├── README.md           # Agent specification and contract
     ├── agent.md            # Claude Code sub-agent format
     ├── src/                # Extracted Python code
     │   ├── __init__.py
     │   ├── core.py         # Main implementation
     │   └── utils.py        # Helper functions
     └── tests/              # Agent-specific tests (if applicable)
     ```

2. **Documentation Standards**
   - **Contract-first approach**: Each agent starts with clear purpose, inputs, outputs, side-effects
   - **Claude Code format**: Proper frontmatter with name, description, tools, imports
   - **Modular references**: Agents reference their extracted code as tools rather than embedding it
   - **Integration documentation**: Clear interfaces for agent-to-agent communication

3. **Code Extraction Strategy**
   - **Identify embedded code**: Scan for Python code blocks within markdown files
   - **Extract systematically**: Move code to appropriate `src/` files within agent directories
   - **Update references**: Modify agent documentation to reference extracted tools
   - **Maintain functionality**: Ensure no breaking changes to existing workflows

### Architecture and Design Decisions

1. **Hierarchical Organization**
   - **Top-level orchestrator**: OrchestratorAgent coordinates everything
   - **Workflow managers**: WorkflowManager handles individual workflows
   - **Specialized agents**: domain-specific agents for particular tasks
   - **Utility agents**: support agents for common operations

2. **Interface Design**
   - **Standard inputs**: All agents accept structured prompts with context
   - **Standard outputs**: Consistent result formats and status reporting
   - **Tool integration**: Clean separation between agent logic and implementation code
   - **Error handling**: Consistent error reporting and recovery patterns

3. **Modularity Principles**
   - **Single responsibility**: Each agent has one clear purpose
   - **Loose coupling**: Agents interact through well-defined interfaces
   - **High cohesion**: Related functionality grouped within agent boundaries
   - **Testability**: Agents designed for easy testing and validation

## Implementation Plan

### Phase 1: Discovery and Analysis (Initial Setup)
**Deliverables**: Agent inventory and extraction plan
- Create target directory structure at `/prompts/Gadugi-v0.3/agents/`
- Scan all agents in `.claude/agents/` and catalog their current state
- Identify agents with embedded Python code requiring extraction
- Map agent relationships and hierarchies
- Create extraction plan prioritizing high-impact agents

### Phase 2: Core Agent Documentation (Foundation)
**Deliverables**: Documentation templates and core agent docs
- Create standardized documentation templates following Claude Code format
- Document top-level agents first (OrchestratorAgent, WorkflowManager)
- Establish consistent patterns for Role, Requirements, Function, Job Description, Tools
- Create example agent documentation to serve as template
- Validate documentation format against Claude Code specifications

### Phase 3: Code Extraction and Modularization (Transformation)
**Deliverables**: Extracted code and updated agent references
- Extract Python code from complex agents (TeamCoach, SystemDesignReviewer, PRBacklogManager)
- Create clean `src/` directory structures within agent folders
- Update agent documentation to reference extracted code as tools
- Test extracted code functionality to ensure no regressions
- Create proper `__init__.py` files and module structures

### Phase 4: Comprehensive Documentation (Completion)
**Deliverables**: Complete agent documentation suite
- Document all remaining agents following established patterns
- Create clear contracts and interface specifications
- Document integration points with shared modules
- Ensure each agent directory is self-contained and well-documented
- Validate documentation completeness and consistency

### Phase 5: Registry and Integration (Finalization)
**Deliverables**: Master registry and validation
- Generate comprehensive `agents.md` file with agent catalog
- Document agent hierarchies and coordination patterns
- Create usage guides and best practices documentation
- Validate all agent documentation for AI comprehension
- Test integration with existing orchestration workflows

## Testing Requirements

### Documentation Validation
- **Format compliance**: All agents follow Claude Code sub-agent specification
- **Completeness check**: Required fields (Role, Requirements, Function, Job Description, Tools) present
- **Contract clarity**: Clear input/output specifications and dependencies documented
- **Integration testing**: Agent references and tool imports work correctly

### Code Extraction Validation
- **Functionality preservation**: Extracted code maintains all original functionality
- **Import resolution**: All module imports and dependencies resolve correctly
- **Interface compatibility**: Agent-to-code interfaces work as documented
- **Test execution**: Any existing tests continue to pass after extraction

### AI Comprehension Testing
- **Agent parsing**: AI agents can understand and work with documented agents
- **Contract adherence**: Interface specifications are clear and actionable
- **Tool integration**: Extracted code can be referenced and used as tools
- **Generation capability**: Documentation supports AI agent creation of similar agents

## Success Criteria

### Measurable Outcomes

1. **Complete Agent Documentation**
   - All 25+ agents documented following consistent format
   - 100% of agents have clear Role, Requirements, Function, Job Description, Tools
   - All agents with embedded Python code successfully extracted to `src/` files
   - Master `agents.md` registry created with comprehensive agent catalog

2. **Modular Architecture Achievement**
   - Each agent exists in self-contained directory with clear contracts
   - Zero embedded Python code in agent markdown files
   - All agents reference extracted code as tools rather than embedding it
   - Clean separation between agent logic and implementation code

3. **AI Integration Readiness**
   - All agent documentation parseable by AI systems
   - Clear contracts enable AI agents to understand and use existing agents
   - Documentation format supports future AI agent generation
   - Integration patterns well-documented for orchestration workflows

4. **Architectural Consistency**
   - Consistent documentation format across all agents
   - Clear hierarchical relationships documented
   - Integration points with shared modules documented
   - Usage patterns and best practices documented

### Quality Metrics

- **Documentation completeness**: 100% of required fields present in all agents
- **Code extraction success**: 100% of embedded Python code extracted successfully
- **Format compliance**: 100% compliance with Claude Code sub-agent specification
- **Integration preservation**: 100% of existing agent functionality preserved

## Implementation Steps

### Step 1: Issue Creation and Branch Management
1. Create GitHub issue titled "Comprehensive Agent Documentation and Refactoring"
2. Include detailed description covering scope, approach, and success criteria
3. Add labels: `documentation`, `refactoring`, `agents`, `architecture`
4. Create feature branch: `docs/comprehensive-agent-documentation`
5. Set up proper attribution for AI agent work

### Step 2: Discovery Phase Execution
1. **Agent inventory creation**:
   - Use `LS` and `Grep` tools to scan `.claude/agents/` directory
   - Catalog all agent files and their current documentation state
   - Identify agents with embedded Python code (search for ```python blocks)
   - Map agent relationships by analyzing import statements and references

2. **Structure preparation**:
   - Create `/prompts/Gadugi-v0.3/agents/` directory structure
   - Plan CamelCase naming convention for agent directories
   - Prepare documentation templates based on Claude Code format
   - Create extraction plan prioritizing complex agents first

### Step 3: Core Agent Documentation
1. **Template creation**:
   - Design standard agent documentation template with all required fields
   - Create example documentation for OrchestratorAgent as reference
   - Establish patterns for contract definition and tool referencing
   - Validate template against Claude Code sub-agent specifications

2. **High-priority agent documentation**:
   - Document OrchestratorAgent with clear hierarchy and coordination role
   - Document WorkflowManager with workflow orchestration capabilities
   - Document key utility agents (WorktreeManager, MemoryManager, etc.)
   - Ensure foundational agents follow established patterns perfectly

### Step 4: Code Extraction Implementation
1. **Complex agent processing**:
   - Extract Python code from TeamCoach agent (substantial codebase in subdirectories)
   - Extract Python code from SystemDesignReviewer agent
   - Extract Python code from PRBacklogManager agent
   - Extract standalone Python files (task-pattern-classifier.py, etc.)

2. **Code organization**:
   - Create proper `src/` directory structures within agent folders
   - Organize extracted code with clear module boundaries
   - Create appropriate `__init__.py` files for proper Python packaging
   - Update agent documentation to reference extracted code as tools

### Step 5: Comprehensive Documentation Completion
1. **Remaining agent documentation**:
   - Process all remaining agents in `.claude/agents/` directory
   - Apply consistent documentation patterns to each agent
   - Ensure each agent has clear contracts and interface definitions
   - Document integration points and dependencies

2. **Quality validation**:
   - Review all agent documentation for completeness and consistency
   - Validate that all required Claude Code fields are present
   - Test that extracted code references work correctly
   - Ensure each agent directory is truly self-contained

### Step 6: Registry Creation and Validation
1. **Master registry generation**:
   - Create comprehensive `agents.md` file cataloging all agents
   - Include agent summaries, capabilities, and use cases
   - Document hierarchical relationships and coordination patterns
   - Add usage examples and best practices

2. **Integration testing**:
   - Test that agent documentation is parseable by AI systems
   - Validate that existing orchestration workflows still function
   - Ensure that extracted code can be properly referenced and executed
   - Verify that all agent interfaces work as documented

### Step 7: Documentation Updates and Final Review
1. **Supporting documentation**:
   - Update project documentation to reference new agent structure
   - Create migration guide for updating existing agent usage
   - Document new patterns for creating agents following established format
   - Add troubleshooting guide for common agent integration issues

2. **Final validation**:
   - Comprehensive review of all agent documentation
   - Testing of extracted code functionality
   - Validation of AI comprehension and usability
   - Integration testing with existing Gadugi workflows

### Step 8: Pull Request and Review Process
1. **PR preparation**:
   - Create comprehensive pull request with detailed description
   - Include before/after comparisons showing improvements
   - Add examples demonstrating new agent structure benefits
   - Include validation results and testing documentation

2. **Review facilitation**:
   - Request review focusing on documentation quality and architectural consistency
   - Demonstrate improved modularity and AI integration capabilities
   - Address any feedback regarding agent interface design
   - Ensure all success criteria are met before final approval

## Additional Considerations

### Backward Compatibility
- Maintain compatibility with existing agent invocation patterns
- Preserve all current agent functionality during refactoring
- Document migration path for any breaking changes
- Provide clear upgrade guidance for agent consumers

### Future Extensibility
- Design agent structure to support easy addition of new agents
- Create patterns that enable AI-assisted agent generation
- Ensure documentation format supports automated agent creation
- Build foundation for advanced agent orchestration capabilities

### Performance Implications
- Minimize impact on agent execution performance
- Ensure extracted code maintains efficient execution patterns
- Design modular structure to support parallel agent development
- Consider caching and optimization opportunities in new structure

### Security Considerations
- Maintain security boundaries in extracted code
- Ensure proper isolation between agent implementations
- Document security considerations for agent interaction patterns
- Preserve existing security validations and audit trails

## Success Validation

This implementation will be considered successful when:

1. **Complete Documentation**: All agents in `.claude/agents/` have been documented following Claude Code format with extracted code properly organized in modular directories
2. **AI Integration**: AI systems can easily understand, reference, and work with all documented agents
3. **Modular Architecture**: Each agent exists as a self-contained "brick" with clear "stud" interfaces following Guidelines.md philosophy
4. **Functional Preservation**: All existing agent functionality is preserved while achieving improved modularity
5. **Comprehensive Registry**: Master `agents.md` provides complete catalog enabling easy agent discovery and understanding
6. **Architectural Consistency**: Consistent patterns across all agents enable predictable integration and extension

The resulting agent architecture will serve as the foundation for future Gadugi development, enabling both human developers and AI agents to easily understand, maintain, and extend the multi-agent system capabilities.
