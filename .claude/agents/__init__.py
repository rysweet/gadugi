# Make agents a Python package

"""
Gadugi Agent Registry

Available Agents:
- OrchestratorAgent: Top-level coordinator for parallel task execution
- WorkflowManager: Orchestrates individual development workflows
- TestSolver: Analyzes and resolves failing tests through systematic analysis
- TestWriter: Authors comprehensive tests for new functionality with TDD alignment
- CodeReviewer: Reviews pull requests with comprehensive analysis
- CodeReviewResponse: Responds to code review feedback
- MemoryManager: Manages Memory.md pruning and GitHub Issues sync
- PromptWriter: Creates structured prompts for workflows
- TaskAnalyzer: Analyzes task dependencies and complexity
- WorktreeManager: Manages git worktrees for parallel development
- ExecutionMonitor: Monitors parallel execution progress
- TeamCoach: Intelligent multi-agent coordination and optimization
- ProgramManager: Project health maintenance and oversight
- XpiaDefenseAgent: Cross-Prompt Injection Attack defense

Test Agents (New):
- TestSolver: Systematic test failure analysis and resolution
- TestWriter: Automated test creation with quality validation
- shared_test_instructions: Shared framework for test quality and consistency

Usage:
    /agent:TestSolver
    Context: Analyze and resolve failing test: tests/test_module.py::test_function

    /agent:TestWriter
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
