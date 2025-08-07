# Enhanced task tracking with shared modules
class WorkflowTaskManager:
    def __init__(self, workflow_state):
        self.todowrite_manager = TodoWriteManager()
        self.task_tracker = TaskTracker()
        self.phase_tracker = WorkflowPhaseTracker()
        self.workflow_state = workflow_state

    def initialize_workflow_tasks(self, prompt_data):
        # Create comprehensive task list with enhanced metadata
        tasks = [
            TaskData(
                id="1",
                content=f"Create GitHub issue for {prompt_data.feature_name}",
                status="pending",
                priority="high",
                phase=WorkflowPhase.ISSUE_CREATION,
                estimated_duration_minutes=5,
                dependencies=[]
            ),
            TaskData(
                id="2",
                content="Create feature branch",
                status="pending",
                priority="high",
                phase=WorkflowPhase.BRANCH_MANAGEMENT,
                estimated_duration_minutes=2,
                dependencies=["1"]
            ),
            TaskData(
                id="3",
                content="Research existing implementation",
                status="pending",
                priority="high",
                phase=WorkflowPhase.RESEARCH_PLANNING,
                estimated_duration_minutes=15,
                dependencies=["2"]
            ),
            TaskData(
                id="4",
                content="Implement core functionality",
                status="pending",
                priority="high",
                phase=WorkflowPhase.IMPLEMENTATION,
                estimated_duration_minutes=45,
                dependencies=["3"]
            ),
            TaskData(
                id="5",
                content="Write comprehensive tests",
                status="pending",
                priority="high",
                phase=WorkflowPhase.TESTING,
                estimated_duration_minutes=30,
                dependencies=["4"]
            ),
            TaskData(
                id="6",
                content="Update documentation",
                status="pending",
                priority="medium",
                phase=WorkflowPhase.DOCUMENTATION,
                estimated_duration_minutes=20,
                dependencies=["4"]
            ),
            TaskData(
                id="7",
                content="Create pull request",
                status="pending",
                priority="high",
                phase=WorkflowPhase.PULL_REQUEST_CREATION,
                estimated_duration_minutes=10,
                dependencies=["5", "6"]
            ),
            TaskData(
                id="8",
                content="Complete code review process",
                status="pending",
                priority="high",
                phase=WorkflowPhase.REVIEW,
                estimated_duration_minutes=15,
                dependencies=["7"]
            )
        ]

        # Initialize with enhanced tracking
        self.task_tracker.initialize_task_list(tasks, self.workflow_state.task_id)
        self.todowrite_manager.create_enhanced_task_list(tasks)

        return tasks

    def update_task_progress(self, task_id, status, progress_notes=None):
        # Enhanced task updates with analytics
        self.task_tracker.update_task_status(
            task_id,
            status,
            workflow_id=self.workflow_state.task_id,
            progress_notes=progress_notes
        )

        # Update TodoWrite with validation
        self.todowrite_manager.update_task_with_validation(task_id, status)

        # Track productivity metrics
        if status == "completed":
            productivity_analyzer.record_task_completion(
                task_id,
                self.workflow_state.task_id,
                duration=self.task_tracker.get_task_duration(task_id)
            )
