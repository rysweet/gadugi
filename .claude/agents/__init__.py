# Make agents a Python package

"""
Gadugi Agent Registry

Available Agents:
- orchestrator-agent: Top-level coordinator for parallel task execution
- workflow-manager: Orchestrates individual development workflows
- test-solver: Analyzes and resolves failing tests through systematic analysis
- test-writer: Authors comprehensive tests for new functionality with TDD alignment
- code-reviewer: Reviews pull requests with comprehensive analysis
- code-review-response: Responds to code review feedback
- memory-manager: Manages Memory.md pruning and GitHub Issues sync
- prompt-writer: Creates structured prompts for workflows
- task-analyzer: Analyzes task dependencies and complexity
- worktree-manager: Manages git worktrees for parallel development
- execution-monitor: Monitors parallel execution progress
- team-coach: Intelligent multi-agent coordination and optimization
- program-manager: Project health maintenance and oversight
- xpia-defense-agent: Cross-Prompt Injection Attack defense

Test Agents (New):
- test-solver: Systematic test failure analysis and resolution
- test-writer: Automated test creation with quality validation
- shared_test_instructions: Shared framework for test quality and consistency

Usage:
    /agent:test-solver
    Context: Analyze and resolve failing test: tests/test_module.py::test_function

    /agent:test-writer
    Context: Create tests for src/module.py with TDD alignment
"""

# Import key agent components for programmatic access
try:
    from .test_solver_agent import TestSolverAgent
    from .test_writer_agent import TestWriterAgent
    from .shared_test_instructions import SharedTestInstructions
    # from .workflow_master_enhanced import  # Module not available EnhancedWorkflowMaster
except ImportError:
    # Graceful degradation if imports fail
    pass

__all__ = [
    "TestSolverAgent",
    "TestWriterAgent",
    "SharedTestInstructions",
    # "EnhancedWorkflowMaster",  # Not available
]
