"""
Pytest configuration and shared fixtures for Gadugi tests.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, Generator


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
    def _mock_response(success: bool = True, data: Dict[str, Any] = None, 
                      raw_output: str = "", error: str = ""):
        return {
            'success': success,
            'data': data,
            'raw_output': raw_output,
            'error': error
        }
    return _mock_response


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for GitHub operations."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"number": 1, "url": "https://github.com/test/repo/issues/1"}'
        mock_run.return_value.stderr = ''
        yield mock_run


@pytest.fixture
def sample_task():
    """Sample task data for testing."""
    return {
        'task_id': 'test-task-001',
        'prompt_file': 'test-feature.md',
        'branch': 'feature/test-feature-001',
        'issue_number': 1,
        'pr_number': None,
        'status': 'pending',
        'created_at': '2025-08-01T22:00:00Z',
        'context': {
            'user_request': 'Add test feature',
            'priority': 'high'
        }
    }


@pytest.fixture
def mock_state_file(temp_dir):
    """Create a mock state file for testing."""
    state_file = temp_dir / 'state.md'
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
        'github': {
            'retry_config': {
                'max_retries': 3,
                'initial_delay': 1,
                'backoff_factor': 2
            }
        },
        'state_management': {
            'state_dir': '.github/workflow-states',
            'cleanup_after_days': 30
        },
        'task_tracking': {
            'todo_write_enabled': True,
            'max_tasks_per_list': 20
        },
        'performance': {
            'monitoring_enabled': True,
            'metrics_retention_days': 7
        }
    }