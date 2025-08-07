"""
WorkflowManager Core Implementation

This module contains the core workflow orchestration logic for systematic execution
of development phases from issue creation through PR review.
"""

import secrets
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Enhanced Separation Architecture - Shared Modules
try:
    from .claude.shared.github_operations import GitHubOperations
    from .claude.shared.state_management import WorkflowStateManager, CheckpointManager, StateBackupRestore
    from .claude.shared.error_handling import ErrorHandler, RetryManager, CircuitBreaker, RecoveryManager
    from .claude.shared.task_tracking import TaskTracker, TodoWriteManager, WorkflowPhaseTracker, ProductivityAnalyzer
    from .claude.shared.interfaces import AgentConfig, PerformanceMetrics, WorkflowState, TaskData, ErrorContext, WorkflowPhase, IssueData, PullRequestData
except ImportError:
    # Fallback for when shared modules are not available
    logging.warning("Shared modules not available, using fallback implementations")


class WorkflowManagerCore:
    """Core workflow management engine for systematic development processes."""
    
    def __init__(self):
        """Initialize shared managers and workflow configuration."""
        # Initialize shared managers for workflow execution
        self.github_ops = GitHubOperations()
        self.state_manager = WorkflowStateManager()
        self.error_handler = ErrorHandler(retry_manager=RetryManager())
        self.task_tracker = TaskTracker(todowrite_manager=TodoWriteManager())
        self.phase_tracker = WorkflowPhaseTracker()
        self.productivity_analyzer = ProductivityAnalyzer()

        # Configure circuit breakers for workflow resilience
        self.github_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)
        self.workflow_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=600)

    def initialize_workflow_task(self, task_id: Optional[str] = None, prompt_file: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced task initialization with shared modules."""
        # Generate unique task ID with enhanced tracking
        if not task_id:
            task_id = f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(2)}"

        # Initialize productivity tracking
        self.productivity_analyzer.start_workflow_tracking(task_id, prompt_file)

        # Check for existing state with enhanced state management
        existing_state = self.state_manager.get_workflow_state(task_id)
        if existing_state:
            logging.info(f"Resuming workflow for task {task_id} from phase {existing_state.current_phase}")
            return existing_state
        
        # Create new workflow state
        workflow_state = WorkflowState(
            task_id=task_id,
            prompt_file=prompt_file,
            current_phase=WorkflowPhase.INITIALIZATION,
            created_at=datetime.now(),
            status="initialized"
        )
        
        # Save initial state
        self.state_manager.save_workflow_state(workflow_state)
        
        return workflow_state

    @error_handler.with_circuit_breaker(github_circuit_breaker)
    def create_workflow_issue(self, workflow_state: 'WorkflowState', prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Issue creation with shared modules and error handling."""
        # Track phase start
        self.phase_tracker.start_phase(WorkflowPhase.ISSUE_CREATION)
        self.productivity_analyzer.record_phase_start("issue_creation")

        # Prepare comprehensive issue data
        issue_data = IssueData(
            title=f"{prompt_data.get('feature_name', 'Development Task')} - {workflow_state.task_id}",
            description=self._generate_issue_description(prompt_data, workflow_state),
            labels=self._determine_issue_labels(prompt_data),
            assignees=prompt_data.get('assignees', []),
            milestone=prompt_data.get('milestone'),
            metadata={
                'task_id': workflow_state.task_id,
                'workflow_phase': 'issue_creation',
                'prompt_file': workflow_state.prompt_file,
                'created_by': 'workflow-manager'
            }
        )

        try:
            # Create issue with retry logic
            issue_result = self.github_ops.create_issue(issue_data)
            
            # Update workflow state
            workflow_state.github_issue = issue_result.number
            workflow_state.current_phase = WorkflowPhase.BRANCH_CREATION
            self.state_manager.save_workflow_state(workflow_state)
            
            # Track phase completion
            self.phase_tracker.complete_phase(WorkflowPhase.ISSUE_CREATION)
            self.productivity_analyzer.record_phase_completion("issue_creation", {
                'issue_number': issue_result.number,
                'labels_count': len(issue_data.labels),
                'creation_success': True
            })
            
            logging.info(f"✅ Issue #{issue_result.number} created successfully for task {workflow_state.task_id}")
            return issue_result
            
        except Exception as e:
            self.error_handler.handle_error(ErrorContext(
                error=e,
                task_id=workflow_state.task_id,
                phase="issue_creation",
                recovery_action="retry_issue_creation"
            ))
            raise

    @error_handler.with_circuit_breaker(github_circuit_breaker)
    def create_workflow_pull_request(self, workflow_state: 'WorkflowState', implementation_summary: Dict[str, Any]) -> Dict[str, Any]:
        """PR creation with shared modules and comprehensive error handling."""
        # Track phase start
        self.phase_tracker.start_phase(WorkflowPhase.PULL_REQUEST_CREATION)
        self.productivity_analyzer.record_phase_start("pr_creation")

        # Prepare comprehensive PR data
        pr_data = PullRequestData(
            title=f"{implementation_summary.get('feature_name', 'Implementation')} - Implementation",
            description=self._generate_pr_description(implementation_summary, workflow_state),
            head_branch=workflow_state.feature_branch,
            base_branch="main",
            labels=self._determine_pr_labels(implementation_summary),
            assignees=implementation_summary.get('assignees', []),
            milestone=implementation_summary.get('milestone'),
            draft=False,
            metadata={
                'task_id': workflow_state.task_id,
                'workflow_phase': 'pr_creation',
                'related_issue': workflow_state.github_issue,
                'implementation_files': implementation_summary.get('modified_files', []),
                'created_by': 'workflow-manager'
            }
        )

        try:
            # Create PR with retry logic
            pr_result = self.github_ops.create_pull_request(pr_data)
            
            # Update workflow state
            workflow_state.github_pr = pr_result.number
            workflow_state.current_phase = WorkflowPhase.REVIEW
            self.state_manager.save_workflow_state(workflow_state)
            
            # Track phase completion
            self.phase_tracker.complete_phase(WorkflowPhase.PULL_REQUEST_CREATION)
            self.productivity_analyzer.record_phase_completion("pr_creation", {
                'pr_number': pr_result.number,
                'files_modified': len(implementation_summary.get('modified_files', [])),
                'related_issue': workflow_state.github_issue,
                'creation_success': True
            })
            
            logging.info(f"✅ PR #{pr_result.number} created successfully for task {workflow_state.task_id}")
            return pr_result
            
        except Exception as e:
            self.error_handler.handle_error(ErrorContext(
                error=e,
                task_id=workflow_state.task_id,
                phase="pr_creation",
                recovery_action="retry_pr_creation"
            ))
            raise

    def _generate_issue_description(self, prompt_data: Dict[str, Any], workflow_state: 'WorkflowState') -> str:
        """Generate comprehensive issue description."""
        description_parts = [
            f"## Task: {prompt_data.get('feature_name', 'Development Task')}",
            f"",
            f"**Task ID**: `{workflow_state.task_id}`",
            f"**Prompt File**: `{workflow_state.prompt_file}`",
            f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"### Requirements",
        ]
        
        # Add requirements from prompt data
        requirements = prompt_data.get('requirements', [])
        if requirements:
            for req in requirements:
                description_parts.append(f"- {req}")
        else:
            description_parts.append("- Requirements to be extracted from prompt file")
        
        description_parts.extend([
            f"",
            f"### Implementation Plan",
            f"This task will be executed through the WorkflowManager's systematic 11-phase process:",
            f"",
            f"1. **Setup & Planning** - Task initialization and state management",
            f"2. **Issue Creation** - This issue (completed)",
            f"3. **Branch Creation** - Feature branch setup",
            f"4. **Research & Analysis** - Requirements analysis and design planning",
            f"5. **Implementation** - Core development work",
            f"6. **Testing** - Comprehensive testing and validation",
            f"7. **Documentation** - Update documentation and guides",
            f"8. **Pull Request** - Create PR with comprehensive context",
            f"9. **Code Review** - Mandatory review via code-reviewer agent",
            f"10. **Review Response** - Address review feedback",
            f"11. **Settings Update** - Update project settings if needed",
            f"",
            f"### Success Criteria",
            f"- [ ] All implementation requirements met",
            f"- [ ] Comprehensive test coverage provided",
            f"- [ ] Documentation updated appropriately",
            f"- [ ] Code review completed and approved",
            f"- [ ] Pull request successfully merged",
            f"",
            f"---",
            f"*This issue was created automatically by the WorkflowManager agent.*"
        ])
        
        return "\n".join(description_parts)

    def _determine_issue_labels(self, prompt_data: Dict[str, Any]) -> List[str]:
        """Determine appropriate labels for the issue."""
        labels = ['workflow-manager', 'ai-generated']
        
        # Add labels based on prompt content
        feature_name = prompt_data.get('feature_name', '').lower()
        if 'test' in feature_name:
            labels.append('testing')
        if 'fix' in feature_name or 'bug' in feature_name:
            labels.append('bug')
        if 'feature' in feature_name or 'implement' in feature_name:
            labels.append('enhancement')
        if 'doc' in feature_name:
            labels.append('documentation')
        
        return labels

    def _generate_pr_description(self, implementation_summary: Dict[str, Any], workflow_state: 'WorkflowState') -> str:
        """Generate comprehensive PR description."""
        description_parts = [
            f"## {implementation_summary.get('feature_name', 'Implementation')}",
            f"",
            f"**Task ID**: `{workflow_state.task_id}`",
            f"**Related Issue**: #{workflow_state.github_issue}",
            f"**Prompt File**: `{workflow_state.prompt_file}`",
            f"",
            f"### Summary",
            implementation_summary.get('summary', 'Implementation completed via WorkflowManager systematic process.'),
            f"",
            f"### Changes Made",
        ]
        
        # Add modified files
        modified_files = implementation_summary.get('modified_files', [])
        if modified_files:
            for file_path in modified_files:
                description_parts.append(f"- `{file_path}`")
        else:
            description_parts.append("- Files modified during implementation")
        
        description_parts.extend([
            f"",
            f"### Testing",
            implementation_summary.get('testing_notes', 'Testing completed as part of systematic workflow process.'),
            f"",
            f"### Documentation",
            implementation_summary.get('documentation_notes', 'Documentation updated as needed.'),
            f"",
            f"### Review Requirements",
            f"- [ ] Code review completed via code-reviewer agent (Phase 9 - MANDATORY)",
            f"- [ ] All review feedback addressed (Phase 10)",
            f"- [ ] CI/CD pipeline passes",
            f"- [ ] No merge conflicts with main branch",
            f"",
            f"### Workflow Status",
            f"This PR was created through WorkflowManager's systematic 11-phase process:",
            f"- ✅ **Phases 1-8**: Setup through PR creation completed",
            f"- 🚨 **Phase 9**: Code review (MANDATORY - will be invoked automatically)",
            f"- ⏳ **Phase 10**: Review response (triggered after review)",
            f"- ⏳ **Phase 11**: Settings update (if applicable)",
            f"",
            f"---",
            f"*This PR was created automatically by the WorkflowManager agent.*",
            f"*Related issue will be closed automatically upon successful merge.*"
        ])
        
        return "\n".join(description_parts)

    def _determine_pr_labels(self, implementation_summary: Dict[str, Any]) -> List[str]:
        """Determine appropriate labels for the PR."""
        labels = ['workflow-manager', 'ai-generated', 'ready-for-review']
        
        # Add labels based on implementation content
        feature_name = implementation_summary.get('feature_name', '').lower()
        if 'test' in feature_name:
            labels.append('testing')
        if 'fix' in feature_name or 'bug' in feature_name:
            labels.append('bugfix')
        if 'feature' in feature_name or 'implement' in feature_name:
            labels.append('feature')
        if 'doc' in feature_name:
            labels.append('documentation')
        
        return labels


class WorkflowTaskManager:
    """Enhanced task tracking with shared modules."""
    
    def __init__(self, workflow_state: 'WorkflowState'):
        self.todowrite_manager = TodoWriteManager()
        self.task_tracker = TaskTracker()
        self.phase_tracker = WorkflowPhaseTracker()
        self.workflow_state = workflow_state

    def initialize_workflow_tasks(self, prompt_data: Dict[str, Any]) -> List['TaskData']:
        """Create comprehensive task list with enhanced metadata."""
        base_tasks = [
            TaskData(
                id="1",
                content="🚀 Initialize workflow and set up task tracking",
                status="completed" if self.workflow_state.current_phase.value > 1 else "pending",
                priority="high",
                phase=WorkflowPhase.INITIALIZATION,
                auto_invoke=False,
                enforcement_level="REQUIRED"
            ),
            TaskData(
                id="2",
                content="📝 Create GitHub issue with comprehensive description",
                status="completed" if self.workflow_state.current_phase.value > 2 else "pending",
                priority="high",
                phase=WorkflowPhase.ISSUE_CREATION,
                auto_invoke=True,
                enforcement_level="REQUIRED"
            ),
            TaskData(
                id="3",
                content="🌿 Create feature branch and set up development environment",
                status="completed" if self.workflow_state.current_phase.value > 3 else "pending",
                priority="high",
                phase=WorkflowPhase.BRANCH_CREATION,
                auto_invoke=True,
                enforcement_level="REQUIRED"
            ),
            TaskData(
                id="4",
                content="🔍 Research requirements and create implementation plan",
                status="completed" if self.workflow_state.current_phase.value > 4 else "pending",
                priority="medium",
                phase=WorkflowPhase.RESEARCH,
                auto_invoke=False,
                enforcement_level="RECOMMENDED"
            ),
            TaskData(
                id="5",
                content="⚡ Implement core functionality and features",
                status="completed" if self.workflow_state.current_phase.value > 5 else "pending",
                priority="high",
                phase=WorkflowPhase.IMPLEMENTATION,
                auto_invoke=False,
                enforcement_level="REQUIRED"
            ),
            TaskData(
                id="6",
                content="🧪 Create and run comprehensive tests",
                status="completed" if self.workflow_state.current_phase.value > 6 else "pending",
                priority="high",
                phase=WorkflowPhase.TESTING,
                auto_invoke=False,
                enforcement_level="REQUIRED"
            ),
            TaskData(
                id="7",
                content="📚 Update documentation and add usage examples",
                status="completed" if self.workflow_state.current_phase.value > 7 else "pending",
                priority="medium",
                phase=WorkflowPhase.DOCUMENTATION,
                auto_invoke=False,
                enforcement_level="RECOMMENDED"
            ),
            TaskData(
                id="8",
                content="🔀 Create pull request with comprehensive description",
                status="completed" if self.workflow_state.current_phase.value > 8 else "pending",
                priority="high",
                phase=WorkflowPhase.PULL_REQUEST_CREATION,
                auto_invoke=True,
                enforcement_level="REQUIRED"
            ),
            TaskData(
                id="9",
                content="🚨 MANDATORY: Invoke code-reviewer agent (Phase 9 - CANNOT SKIP)",
                status="pending",
                priority="high",  # Maximum priority
                phase=WorkflowPhase.REVIEW,
                auto_invoke=True,  # Flag for automatic execution
                enforcement_level="CRITICAL"  # New enforcement level
            ),
            TaskData(
                id="10",
                content="🚨 MANDATORY: Process review with code-review-response agent",
                status="pending",
                priority="high",  # Maximum priority
                phase=WorkflowPhase.REVIEW_RESPONSE,
                auto_invoke=True,  # Flag for automatic execution
                enforcement_level="CRITICAL"  # New enforcement level
            ),
            TaskData(
                id="11",
                content="🔧 AUTOMATIC: Update Claude settings (Phase 11)",
                status="pending",
                priority="medium",
                phase=WorkflowPhase.SETTINGS_UPDATE,
                auto_invoke=True,
                enforcement_level="OPTIONAL"  # Settings update is beneficial but not critical
            )
        ]
        
        # Create tasks via TodoWrite integration
        for task in base_tasks:
            self.todowrite_manager.create_task(task)
        
        return base_tasks

    def transition_task_status(self, task_id: str, new_status: str) -> bool:
        """Enhanced status transitions with validation."""
        try:
            # Validate transition is allowed
            current_task = self.task_tracker.get_task(task_id)
            if not self.task_tracker.is_valid_transition(current_task.status, new_status):
                raise TaskTransitionError(f"Invalid transition: {current_task.status} -> {new_status}")

            # Check dependencies for in_progress transitions
            if new_status == "in_progress":
                unmet_dependencies = self.task_tracker.check_dependencies(task_id)
                if unmet_dependencies:
                    raise DependencyError(f"Cannot start task {task_id}: unmet dependencies {unmet_dependencies}")

            # Execute transition
            success = self.task_tracker.update_task_status(task_id, new_status)
            
            if success:
                # Update workflow state if this is a phase transition
                current_task = self.task_tracker.get_task(task_id)
                if hasattr(current_task, 'phase') and new_status == "completed":
                    self.phase_tracker.complete_phase(current_task.phase)
                    
                    # Update workflow state current phase
                    next_phase_value = current_task.phase.value + 1
                    if next_phase_value <= 11:  # Max phase number
                        self.workflow_state.current_phase = WorkflowPhase(next_phase_value)
                        # Save updated workflow state
                        # Note: This would use the state_manager in actual implementation
                        
            return success
            
        except Exception as e:
            logging.error(f"Error transitioning task {task_id} to {new_status}: {e}")
            return False

    def get_workflow_progress(self) -> Dict[str, Any]:
        """Get comprehensive workflow progress summary."""
        tasks = self.task_tracker.get_all_tasks()
        
        completed_tasks = [t for t in tasks if t.status == "completed"]
        in_progress_tasks = [t for t in tasks if t.status == "in_progress"]
        pending_tasks = [t for t in tasks if t.status == "pending"]
        
        return {
            'task_id': self.workflow_state.task_id,
            'current_phase': self.workflow_state.current_phase.name,
            'total_tasks': len(tasks),
            'completed_tasks': len(completed_tasks),
            'in_progress_tasks': len(in_progress_tasks),
            'pending_tasks': len(pending_tasks),
            'completion_percentage': (len(completed_tasks) / len(tasks)) * 100 if tasks else 0,
            'next_critical_task': self._find_next_critical_task(tasks),
            'phase_progress': self.phase_tracker.get_phase_progress(),
            'estimated_completion': self._estimate_completion_time(tasks)
        }

    def _find_next_critical_task(self, tasks: List['TaskData']) -> Optional[str]:
        """Find the next critical task that needs attention."""
        # Look for critical enforcement level tasks first
        critical_pending = [t for t in tasks if t.enforcement_level == "CRITICAL" and t.status == "pending"]
        if critical_pending:
            return critical_pending[0].content
        
        # Look for required tasks
        required_pending = [t for t in tasks if t.enforcement_level == "REQUIRED" and t.status == "pending"]
        if required_pending:
            return required_pending[0].content
        
        # Look for any pending tasks
        pending_tasks = [t for t in tasks if t.status == "pending"]
        if pending_tasks:
            return pending_tasks[0].content
        
        return None

    def _estimate_completion_time(self, tasks: List['TaskData']) -> Optional[str]:
        """Estimate remaining completion time based on task complexity."""
        # This would use historical data in a real implementation
        remaining_tasks = [t for t in tasks if t.status != "completed"]
        
        if not remaining_tasks:
            return "Complete"
        
        # Simple estimation based on task count and type
        critical_tasks = len([t for t in remaining_tasks if t.enforcement_level == "CRITICAL"])
        required_tasks = len([t for t in remaining_tasks if t.enforcement_level == "REQUIRED"])
        
        estimated_minutes = (critical_tasks * 15) + (required_tasks * 10) + (len(remaining_tasks) * 5)
        
        if estimated_minutes < 60:
            return f"~{estimated_minutes} minutes"
        else:
            hours = estimated_minutes // 60
            minutes = estimated_minutes % 60
            return f"~{hours}h {minutes}m"


# Exception classes
class TaskTransitionError(Exception):
    """Invalid task status transition."""
    pass

class DependencyError(Exception):
    """Task dependencies not met."""
    pass