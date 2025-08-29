from unittest.mock import patch

"""Test orchestrator governance compliance with Issue #148.

This test ensures the orchestrator properly delegates all task execution
to WorkflowManager instances and never executes tasks directly.
"""

import tempfile
from pathlib import Path

import pytest
import sys
import os

# Add claude directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), ".claude"))

from agents.orchestrator.governance_validator import (  # type: ignore[import-not-found]
    GovernanceValidator,
    validate_orchestrator_compliance,
)
from agents.orchestrator.orchestrator import Orchestrator, TaskDefinition  # type: ignore[import-not-found]
from agents.orchestrator.parallel_executor import ParallelExecutor  # type: ignore[import-not-found]


class TestOrchestratorGovernance:
    """Test suite for orchestrator governance compliance."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator instance for testing."""
        return Orchestrator(
            max_parallel_tasks=2,
            enable_worktrees=True,
        )

    @pytest.fixture
    def parallel_executor(self):
        """Create a parallel executor for testing."""
        return ParallelExecutor(
            max_workers=2,
            enable_worktrees=True,
        )

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return TaskDefinition(
            id="test-task-001",
            name="Test Task",
            description="A test task for governance validation",
            parameters={
                "prompt_file": "/prompts/test-prompt.md",
                "action": "implement",
            },
        )

    def test_governance_validator_initialization(self):
        """Test that governance validator initializes correctly."""
        validator = GovernanceValidator()
        assert validator.violations == []
        assert validator.execution_logs == []

    def test_detect_direct_execution_violation(self):
        """Test detection of direct task execution violations."""
        validator = GovernanceValidator()

        # Simulate direct execution without WorkflowManager
        compliant = validator.validate_task_execution(
            task_id="test-001",
            execution_method="direct",
            execution_details={
                "workflow_manager_invoked": False,
                "result": "Executed directly",
            },
        )

        assert not compliant
        assert len(validator.violations) == 1
        assert validator.violations[0].violation_type == "DIRECT_EXECUTION"  # type: ignore[index]
        assert validator.violations[0].severity == "CRITICAL"  # type: ignore[index]

    def test_detect_incomplete_phases_violation(self):
        """Test detection of incomplete workflow phases."""
        validator = GovernanceValidator()

        # Simulate WorkflowManager invocation with incomplete phases
        compliant = validator.validate_task_execution(
            task_id="test-002",
            execution_method="workflow_manager",
            execution_details={
                "workflow_manager_invoked": True,
                "all_phases_executed": False,
                "phases_completed": ["Phase 1", "Phase 2", "Phase 3"],
            },
        )

        assert not compliant
        assert len(validator.violations) == 1
        assert validator.violations[0].violation_type == "INCOMPLETE_PHASES"  # type: ignore[index]
        assert validator.violations[0].severity == "ERROR"  # type: ignore[index]

    def test_compliant_execution(self):
        """Test that compliant execution passes validation."""
        validator = GovernanceValidator()

        # Simulate proper WorkflowManager delegation with all phases
        compliant = validator.validate_task_execution(
            task_id="test-003",
            execution_method="workflow_manager",
            execution_details={
                "workflow_manager_invoked": True,
                "all_phases_executed": True,
                "phases_completed": [f"Phase {i}" for i in range(1, 12)],
            },
        )

        assert compliant
        assert len(validator.violations) == 0

    def test_code_compliance_validation(self):
        """Test code compliance validation."""
        validator = GovernanceValidator()

        # Create a temporary file with non-compliant code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
            async def _execute_single_task(self, task):
                # Direct execution - VIOLATION
                await asyncio.sleep(0.1)  # Simulate work
                return "Task executed successfully"
            """)
            temp_path = Path(f.name)

        try:
            compliant, issues = validator.validate_code_compliance(temp_path)
            assert not compliant
            assert any("direct execution pattern" in issue for issue in issues)
        finally:
            temp_path.unlink()

    def test_code_compliance_with_delegation(self):
        """Test that code with proper delegation passes validation."""
        validator = GovernanceValidator()

        # Create a temporary file with compliant code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
            async def _execute_single_task(self, task):
                # Proper delegation to WorkflowManager
                result = await self._invoke_workflow_manager(task)
                return result

            async def _invoke_workflow_manager(self, task):
                # Use claude -p for proper subprocess invocation
                cmd = ["claude", "-p", prompt_file]
                # ... execution logic ...
                return result
            """)
            temp_path = Path(f.name)

        try:
            compliant, issues = validator.validate_code_compliance(temp_path)
            assert compliant or len(issues) == 0  # Should be mostly compliant
        finally:
            temp_path.unlink()

    def test_governance_report_generation(self):
        """Test generation of governance compliance report."""
        validator = GovernanceValidator()

        # Simulate execution history
        execution_history = [
            {
                "task_id": "task-001",
                "method": "workflow_manager",
                "details": {
                    "workflow_manager_invoked": True,
                    "all_phases_executed": True,
                },
            },
            {
                "task_id": "task-002",
                "method": "direct",
                "details": {
                    "workflow_manager_invoked": False,
                },
            },
        ]

        report = validator.generate_report(execution_history)

        assert not report.compliant
        assert report.workflow_manager_invocations == 1
        assert report.direct_executions == 1
        assert len(report.violations) > 0
        assert len(report.warnings) > 0

    def test_compliance_enforcement(self):
        """Test that compliance can be enforced on execution details."""
        validator = GovernanceValidator()

        # Original non-compliant execution details
        original_details = {
            "workflow_manager_invoked": False,
            "method": "direct",
        }

        # Enforce compliance
        enforced_details = validator.enforce_compliance("task-001", original_details)

        assert enforced_details["workflow_manager_invoked"] is True  # type: ignore[index]
        assert enforced_details["delegation_enforced"] is True  # type: ignore[index]
        assert "Issue #148" in enforced_details["enforcement_reason"]  # type: ignore[index]
        assert enforced_details["require_all_phases"] is True  # type: ignore[index]
        assert len(enforced_details["required_phases"]) == 11  # type: ignore[index]

    @pytest.mark.asyncio
    async def test_parallel_executor_creates_workflow_prompt(self, parallel_executor, sample_task):
        """Test that parallel executor creates proper workflow prompts."""
        prompt_content = parallel_executor._create_workflow_prompt(sample_task)

        assert "WorkflowManager Task Execution Request" in prompt_content
        assert "GOVERNANCE NOTICE" in prompt_content
        assert "Issue #148" in prompt_content
        assert "11-phase workflow" in prompt_content
        assert "/agent:WorkflowManager" in prompt_content
        assert sample_task.id in prompt_content
        assert sample_task.name in prompt_content

    @pytest.mark.asyncio
    async def test_parallel_executor_invokes_workflow_manager(self, parallel_executor, sample_task):
        """Test that parallel executor properly invokes WorkflowManager."""
        # Mock subprocess execution
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()  # type: ignore[assignment]
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(  # type: ignore[assignment]
                return_value=(
                    b"Phase 1 completed\nPhase 2 completed\n...Phase 11 completed\nPR #123 created",
                    b"",
                )
            )
            mock_subprocess.return_value = mock_process

            result = await parallel_executor._invoke_workflow_manager(sample_task)

            assert result["success"] is True  # type: ignore[index]
            assert result["workflow_manager_invoked"] is True  # type: ignore[index]
            assert result["task_id"] == sample_task.id  # type: ignore[index]

            # Verify claude -p was called
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0]
            assert call_args[0] == "claude"  # type: ignore[index]
            assert call_args[1] == "-p"  # type: ignore[index]

    @pytest.mark.asyncio
    async def test_orchestrator_delegates_to_workflow_manager(self, orchestrator):
        """Test that orchestrator properly delegates tasks to WorkflowManager."""
        # Mock the parallel executor's workflow manager invocation
        with patch.object(
            orchestrator.parallel_executor,
            "_invoke_workflow_manager",
            new_callable=AsyncMock,  # type: ignore[assignment]
        ) as mock_invoke:
            mock_invoke.return_value = {
                "success": True,
                "workflow_manager_invoked": True,
                "all_phases_executed": True,
                "task_id": "test-001",
            }

            # Create and execute a task
            task = TaskDefinition(
                id="test-001",
                name="Test Task",
                description="Test task for delegation",
            )

            result = await orchestrator.parallel_executor._execute_single_task(task)

            assert result.success is True
            mock_invoke.assert_called_once_with(task)

    def test_validate_orchestrator_compliance_integration(self):
        """Integration test for orchestrator compliance validation."""
        # This would check actual files if they exist
        report = validate_orchestrator_compliance()

        # Report should be generated (may or may not be compliant depending on actual files)
        assert report is not None  # type: ignore[comparison-overlap]
        assert hasattr(report, "compliant")
        assert hasattr(report, "violations")
        assert hasattr(report, "workflow_manager_invocations")
        assert hasattr(report, "direct_executions")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
