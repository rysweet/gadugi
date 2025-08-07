"""
Fallback implementations for shared modules during development/testing

Provides basic implementations when Enhanced Separation shared modules
are not available, ensuring the system design reviewer can still function.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum


class ErrorCategory(Enum):
    """Error categories for fallback error handler"""
    GITHUB_API = "github_api"
    FILE_SYSTEM = "file_system"
    PROCESS_EXECUTION = "process_execution"
    STATE_MANAGEMENT = "state_management"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GitHubOperations:
    """Fallback GitHub operations implementation"""

    def __init__(self, task_id=None):
        self.cache = {}
        self.task_id = task_id

    def get_pr_details(self, pr_number: str) -> Dict[str, Any]:
        """Get PR details using GitHub CLI"""
        try:
            cmd = f"gh pr view {pr_number} --json number,title,body,author,baseRefName,headRefName"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"Error getting PR details: {result.stderr}")
                return {}

        except Exception as e:
            print(f"Error getting PR details: {e}")
            return {}

    def post_pr_review(self, pr_number: str, action: str, body: str) -> bool:
        """Post PR review using GitHub CLI"""
        try:
            action_map = {
                "APPROVE": "--approve",
                "REQUEST_CHANGES": "--request-changes",
                "COMMENT": "--comment"
            }

            action_flag = action_map.get(action, "--comment")

            cmd = ["gh", "pr", "review", pr_number, action_flag, "--body", body]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print(f"Successfully posted review for PR #{pr_number}")
                return True
            else:
                print(f"Error posting review: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error posting PR review: {e}")
            return False


class StateManager:
    """Fallback state manager implementation"""

    def __init__(self, state_dir: Path = None, task_id: str = "fallback"):
        self.state_dir = state_dir or Path(".github/workflow-states/system-design-reviewer")
        self.task_id = task_id
        self.state_file = self.state_dir / "fallback_state.json"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_state(self, state_data: Dict[str, Any]) -> bool:
        """Save state to file"""
        try:
            state_data['last_updated'] = datetime.now().isoformat()
            state_data['task_id'] = self.task_id

            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_state(self) -> Dict[str, Any]:
        """Load state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            return self.get_default_state()
        except Exception as e:
            print(f"Error loading state: {e}")
            return self.get_default_state()

    def get_default_state(self) -> Dict[str, Any]:
        """Get default state structure"""
        return {
            'active_reviews': {},
            'completed_reviews': [],
            'performance_metrics': {
                'total_reviews': 0,
                'average_review_time': 0
            }
        }

    def save_review_result(self, result) -> bool:
        """Save review result to state"""
        try:
            state = self.load_state()
            state['completed_reviews'].append(result.to_dict())

            # Keep only last 50 reviews
            if len(state['completed_reviews']) > 50:
                state['completed_reviews'] = state['completed_reviews'][-50:]

            return self.save_state(state)
        except Exception as e:
            print(f"Error saving review result: {e}")
            return False


class ErrorHandler:
    """Fallback error handler implementation"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.error_history = []

    def handle_error(self, exception: Exception, category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle error with basic logging"""
        error_info = {
            'agent_type': self.agent_type,
            'category': category.value,
            'severity': severity.value,
            'message': str(exception),
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }

        self.error_history.append(error_info)

        # Basic logging to console
        print(f"ERROR [{self.agent_type}]: {exception}")
        if context:
            print(f"Context: {context}")

        return error_info


class TaskTracker:
    """Fallback task tracker implementation"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.tasks = {}

    def create_task(self, task_id: str, content: str, priority: str = "medium") -> Dict[str, Any]:
        """Create a new task"""
        task = {
            'id': task_id,
            'content': content,
            'status': 'pending',
            'priority': priority,
            'created_at': datetime.now().isoformat()
        }
        self.tasks[task_id] = task
        print(f"Created task: {content}")
        return task

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = status
            self.tasks[task_id]['updated_at'] = datetime.now().isoformat()
            print(f"Updated task {task_id}: {status}")
            return True
        return False

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        return self.tasks.get(task_id)
