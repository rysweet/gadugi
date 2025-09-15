"""
Pytest configuration and shared fixtures for Gadugi tests.
"""

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from unittest.mock import patch

import pytest

# Add parent directory to Python path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Add src directory where all the code now lives
src_dir = parent_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_gh_response():
    """Mock GitHub CLI response."""

    def _mock_response(
        success: bool = True,
        data: Optional[Dict[str, Any]] = None,
        raw_output: str = "",
        error: str = "",
    ):
        return {
            "success": success,
            "data": data if data is not None else {},
            "raw_output": raw_output,
            "error": error,
        }

    return _mock_response


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for GitHub operations."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '{"number": 1, "url": "https://github.com/test/repo/issues/1"}'
        )
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def sample_task():
    """Sample task data for testing."""
    return {
        "task_id": "test-task-001",
        "prompt_file": "test-feature.md",
        "branch": "feature/test-feature-001",
        "issue_number": 1,
        "pr_number": None,
        "status": "pending",
        "created_at": "2025-08-01T22:00:00Z",
        "context": {"user_request": "Add test feature", "priority": "high"},
    }


@pytest.fixture
def mock_state_file(temp_dir):
    """Create a mock state file for testing."""
    state_file = temp_dir / "state.md"
    state_content = """# WorkflowMaster State
Task ID: test-task-001
Last Updated: 2025-08-01T22:00:00Z

## Active Workflow
- **Task ID**: test-task-001
- **Prompt File**: `/prompts/test-feature.md`
- **Issue Number**: #1
- **Branch**: `feature/test-feature-001`
- **Started**: 2025-08-01T22:00:00Z

## Phase Completion Status
- [x] Phase 1: Initial Setup ✅
- [x] Phase 2: Issue Creation (#1) ✅
- [x] Phase 3: Branch Management (feature/test-feature-001) ✅
- [ ] Phase 4: Research and Planning
- [ ] Phase 5: Implementation
- [ ] Phase 6: Testing
- [ ] Phase 7: Documentation
- [ ] Phase 8: Pull Request
- [ ] Phase 9: Review

## Current Phase Details
### Phase: Research and Planning
- **Status**: in_progress
- **Progress**: Analyzing existing codebase
- **Next Steps**: Identify modules to modify
- **Blockers**: None

## TodoWrite Task IDs
- Current task list IDs: [1, 2, 3, 4, 5, 6, 7, 8, 9]
- Completed tasks: [1, 2, 3]
- In-progress task: 4

## Resumption Instructions
1. Check out branch: `git checkout feature/test-feature-001`
2. Review completed work: setup and issue creation
3. Continue from: Phase 4 - Research and Planning
4. Complete remaining phases: [4-9]
"""
    state_file.write_text(state_content)
    return state_file


@pytest.fixture
def mock_config():
    """Sample configuration for testing."""
    return {
        "github": {"retry_config": {"max_retries": 3, "initial_delay": 1, "backoff_factor": 2}},
        "state_management": {
            "state_dir": ".github/workflow-states",
            "cleanup_after_days": 30,
        },
        "task_tracking": {"todo_write_enabled": True, "max_tasks_per_list": 20},
        "performance": {"monitoring_enabled": True, "metrics_retention_days": 7},
    }


def is_neo4j_running() -> bool:
    """Check if Neo4j container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return "gadugi-neo4j" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def start_neo4j_service() -> bool:
    """Start Neo4j service using the manage-services script."""
    script_path = Path(__file__).parent.parent.parent / ".claude" / "scripts" / "manage-services.sh"

    if not script_path.exists():
        print(f"Service management script not found: {script_path}")
        return False

    try:
        # Start Neo4j using the service management script
        result = subprocess.run(
            [str(script_path), "start", "neo4j"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(f"Failed to start Neo4j: {result.stderr}")
            return False

        # Wait for Neo4j to be ready (max 30 seconds)
        for _ in range(30):
            try:
                # Check if Bolt port is accessible
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", 7689))
                sock.close()

                if result == 0:
                    print("Neo4j is ready on port 7689 (Bolt)")
                    return True
            except Exception:
                pass

            time.sleep(1)

        print("Neo4j started but not responding after 30 seconds")
        return False

    except subprocess.TimeoutExpired:
        print("Timeout while starting Neo4j")
        return False
    except Exception as e:
        print(f"Error starting Neo4j: {e}")
        return False


@pytest.fixture(scope="session")
def ensure_neo4j():
    """Ensure Neo4j is running for tests that need it."""
    if not is_neo4j_running():
        print("Neo4j not running, attempting to start...")
        if not start_neo4j_service():
            pytest.skip("Neo4j service could not be started")
    else:
        print("Neo4j is already running")

    yield

    # Note: We don't stop Neo4j after tests as other tests might need it
    # and it's useful to keep running for development
