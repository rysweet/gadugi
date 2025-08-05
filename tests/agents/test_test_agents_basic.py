"""
Basic tests for Test Solver and Test Writer agents - import and initialization.
"""

import pytest
import sys
import os

# Add agents to path for testing
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "agents")
)


def test_shared_test_instructions_import():
    """Test that shared test instructions can be imported."""
    try:
        from shared_test_instructions import (
            SharedTestInstructions,
            TestStatus,
            SkipReason,
        )

        assert SharedTestInstructions is not None
        assert TestStatus.PASS is not None
        assert SkipReason.API_KEY_MISSING is not None
    except ImportError as e:
        pytest.fail(f"Failed to import shared_test_instructions: {e}")


def test_test_solver_agent_import():
    """Test that TestSolverAgent can be imported."""
    try:
        from test_solver_agent import TestSolverAgent, FailureCategory

        assert TestSolverAgent is not None
        assert FailureCategory.ASSERTION_ERROR is not None
    except ImportError as e:
        pytest.fail(f"Failed to import test_solver_agent: {e}")


def test_test_writer_agent_import():
    """Test that TestWriterAgent can be imported."""
    try:
        from test_writer_agent import TestWriterAgent, TestType

        assert TestWriterAgent is not None
        assert TestType.UNIT is not None
    except ImportError as e:
        pytest.fail(f"Failed to import test_writer_agent: {e}")


def test_test_solver_initialization():
    """Test TestSolverAgent initialization."""
    try:
        from test_solver_agent import TestSolverAgent

        solver = TestSolverAgent()
        assert solver.config is not None
        assert solver.shared_instructions is not None
    except Exception as e:
        pytest.fail(f"Failed to initialize TestSolverAgent: {e}")


def test_test_writer_initialization():
    """Test TestWriterAgent initialization."""
    try:
        from test_writer_agent import TestWriterAgent

        writer = TestWriterAgent()
        assert writer.config is not None
        assert writer.shared_instructions is not None
    except Exception as e:
        pytest.fail(f"Failed to initialize TestWriterAgent: {e}")


def test_shared_instructions_basic_functionality():
    """Test basic functionality of SharedTestInstructions."""
    try:
        from shared_test_instructions import SharedTestInstructions

        # Test basic method existence
        assert hasattr(SharedTestInstructions, "analyze_test_purpose")
        assert hasattr(SharedTestInstructions, "validate_test_structure")
        assert hasattr(SharedTestInstructions, "ensure_test_idempotency")

        # Test basic functionality
        test_code = "def test_example(): assert True"
        analysis = SharedTestInstructions.analyze_test_purpose(test_code)
        assert analysis is not None
        assert hasattr(analysis, "purpose")

    except Exception as e:
        pytest.fail(f"SharedTestInstructions basic functionality failed: {e}")


def test_agent_config_fallback():
    """Test that agents work with fallback config when enhanced separation is not available."""
    try:
        from test_solver_agent import TestSolverAgent
        from test_writer_agent import TestWriterAgent

        # Should work even if enhanced separation modules are not available
        solver = TestSolverAgent()
        writer = TestWriterAgent()

        assert solver.config.agent_id == "test_solver_agent"
        assert writer.config.agent_id == "test_writer_agent"

    except Exception as e:
        pytest.fail(f"Agent fallback configuration failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
