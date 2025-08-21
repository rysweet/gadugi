import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TaskStarted(_message.Message):
    __slots__ = ("task_id", "parent_task_id", "workflow_id", "agent_id", "task_type", "task_name", "description", "timestamp", "priority", "parameters", "metadata", "resources", "timeout_seconds", "dependencies")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_TASK_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TASK_TYPE_FIELD_NUMBER: _ClassVar[int]
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    parent_task_id: str
    workflow_id: str
    agent_id: str
    task_type: str
    task_name: str
    description: str
    timestamp: _common_pb2.Timestamp
    priority: _common_pb2.Priority
    parameters: _containers.ScalarMap[str, str]
    metadata: _common_pb2.Metadata
    resources: _common_pb2.ResourceRequirements
    timeout_seconds: int
    dependencies: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, task_id: _Optional[str] = ..., parent_task_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., task_type: _Optional[str] = ..., task_name: _Optional[str] = ..., description: _Optional[str] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., priority: _Optional[_Union[_common_pb2.Priority, str]] = ..., parameters: _Optional[_Mapping[str, str]] = ..., metadata: _Optional[_Union[_common_pb2.Metadata, _Mapping]] = ..., resources: _Optional[_Union[_common_pb2.ResourceRequirements, _Mapping]] = ..., timeout_seconds: _Optional[int] = ..., dependencies: _Optional[_Iterable[str]] = ...) -> None: ...

class TaskProgress(_message.Message):
    __slots__ = ("task_id", "agent_id", "percent_complete", "status_message", "timestamp", "completed_steps", "remaining_steps", "elapsed_ms", "estimated_remaining_ms", "metrics", "current_phase")
    class MetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    PERCENT_COMPLETE_FIELD_NUMBER: _ClassVar[int]
    STATUS_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_STEPS_FIELD_NUMBER: _ClassVar[int]
    REMAINING_STEPS_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_MS_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_REMAINING_MS_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PHASE_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    percent_complete: int
    status_message: str
    timestamp: _common_pb2.Timestamp
    completed_steps: _containers.RepeatedScalarFieldContainer[str]
    remaining_steps: _containers.RepeatedScalarFieldContainer[str]
    elapsed_ms: int
    estimated_remaining_ms: int
    metrics: _containers.ScalarMap[str, float]
    current_phase: str
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., percent_complete: _Optional[int] = ..., status_message: _Optional[str] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., completed_steps: _Optional[_Iterable[str]] = ..., remaining_steps: _Optional[_Iterable[str]] = ..., elapsed_ms: _Optional[int] = ..., estimated_remaining_ms: _Optional[int] = ..., metrics: _Optional[_Mapping[str, float]] = ..., current_phase: _Optional[str] = ...) -> None: ...

class TaskCompleted(_message.Message):
    __slots__ = ("task_id", "agent_id", "timestamp", "success_message", "output_data", "outputs", "duration_ms", "metadata", "performance_metrics", "retry_count", "artifacts")
    class OutputsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class PerformanceMetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_DATA_FIELD_NUMBER: _ClassVar[int]
    OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    PERFORMANCE_METRICS_FIELD_NUMBER: _ClassVar[int]
    RETRY_COUNT_FIELD_NUMBER: _ClassVar[int]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    timestamp: _common_pb2.Timestamp
    success_message: str
    output_data: bytes
    outputs: _containers.ScalarMap[str, str]
    duration_ms: int
    metadata: _common_pb2.Metadata
    performance_metrics: _containers.ScalarMap[str, float]
    retry_count: int
    artifacts: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., success_message: _Optional[str] = ..., output_data: _Optional[bytes] = ..., outputs: _Optional[_Mapping[str, str]] = ..., duration_ms: _Optional[int] = ..., metadata: _Optional[_Union[_common_pb2.Metadata, _Mapping]] = ..., performance_metrics: _Optional[_Mapping[str, float]] = ..., retry_count: _Optional[int] = ..., artifacts: _Optional[_Iterable[str]] = ...) -> None: ...

class TaskFailed(_message.Message):
    __slots__ = ("task_id", "agent_id", "timestamp", "error", "retriable", "retry_count", "recovery_suggestion", "duration_ms", "failure_phase", "partial_outputs", "debug_info")
    class DebugInfoEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    RETRIABLE_FIELD_NUMBER: _ClassVar[int]
    RETRY_COUNT_FIELD_NUMBER: _ClassVar[int]
    RECOVERY_SUGGESTION_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    FAILURE_PHASE_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    DEBUG_INFO_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    timestamp: _common_pb2.Timestamp
    error: _common_pb2.Error
    retriable: bool
    retry_count: int
    recovery_suggestion: str
    duration_ms: int
    failure_phase: str
    partial_outputs: _containers.RepeatedScalarFieldContainer[str]
    debug_info: _containers.ScalarMap[str, str]
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., error: _Optional[_Union[_common_pb2.Error, _Mapping]] = ..., retriable: bool = ..., retry_count: _Optional[int] = ..., recovery_suggestion: _Optional[str] = ..., duration_ms: _Optional[int] = ..., failure_phase: _Optional[str] = ..., partial_outputs: _Optional[_Iterable[str]] = ..., debug_info: _Optional[_Mapping[str, str]] = ...) -> None: ...

class TaskCancelled(_message.Message):
    __slots__ = ("task_id", "agent_id", "reason", "timestamp", "cancelled_by", "force_cancelled", "state_at_cancellation", "percent_complete")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    CANCELLED_BY_FIELD_NUMBER: _ClassVar[int]
    FORCE_CANCELLED_FIELD_NUMBER: _ClassVar[int]
    STATE_AT_CANCELLATION_FIELD_NUMBER: _ClassVar[int]
    PERCENT_COMPLETE_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    reason: str
    timestamp: _common_pb2.Timestamp
    cancelled_by: str
    force_cancelled: bool
    state_at_cancellation: str
    percent_complete: int
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., reason: _Optional[str] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., cancelled_by: _Optional[str] = ..., force_cancelled: bool = ..., state_at_cancellation: _Optional[str] = ..., percent_complete: _Optional[int] = ...) -> None: ...

class TaskPaused(_message.Message):
    __slots__ = ("task_id", "agent_id", "reason", "timestamp", "paused_by", "checkpoint_data", "percent_complete", "can_resume")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PAUSED_BY_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINT_DATA_FIELD_NUMBER: _ClassVar[int]
    PERCENT_COMPLETE_FIELD_NUMBER: _ClassVar[int]
    CAN_RESUME_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    reason: str
    timestamp: _common_pb2.Timestamp
    paused_by: str
    checkpoint_data: bytes
    percent_complete: int
    can_resume: bool
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., reason: _Optional[str] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., paused_by: _Optional[str] = ..., checkpoint_data: _Optional[bytes] = ..., percent_complete: _Optional[int] = ..., can_resume: bool = ...) -> None: ...

class TaskResumed(_message.Message):
    __slots__ = ("task_id", "agent_id", "timestamp", "resumed_by", "pause_duration_ms", "checkpoint_data")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    RESUMED_BY_FIELD_NUMBER: _ClassVar[int]
    PAUSE_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINT_DATA_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    timestamp: _common_pb2.Timestamp
    resumed_by: str
    pause_duration_ms: int
    checkpoint_data: bytes
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., resumed_by: _Optional[str] = ..., pause_duration_ms: _Optional[int] = ..., checkpoint_data: _Optional[bytes] = ...) -> None: ...

class TaskDependencyUpdate(_message.Message):
    __slots__ = ("task_id", "depends_on", "blocks", "ready_dependencies", "waiting_on", "timestamp", "all_dependencies_met")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    DEPENDS_ON_FIELD_NUMBER: _ClassVar[int]
    BLOCKS_FIELD_NUMBER: _ClassVar[int]
    READY_DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    WAITING_ON_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ALL_DEPENDENCIES_MET_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    depends_on: _containers.RepeatedScalarFieldContainer[str]
    blocks: _containers.RepeatedScalarFieldContainer[str]
    ready_dependencies: _containers.RepeatedScalarFieldContainer[str]
    waiting_on: _containers.RepeatedScalarFieldContainer[str]
    timestamp: _common_pb2.Timestamp
    all_dependencies_met: bool
    def __init__(self, task_id: _Optional[str] = ..., depends_on: _Optional[_Iterable[str]] = ..., blocks: _Optional[_Iterable[str]] = ..., ready_dependencies: _Optional[_Iterable[str]] = ..., waiting_on: _Optional[_Iterable[str]] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., all_dependencies_met: bool = ...) -> None: ...

class TaskRetrying(_message.Message):
    __slots__ = ("task_id", "agent_id", "attempt_number", "max_attempts", "timestamp", "previous_error", "delay_ms", "retry_strategy")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ATTEMPT_NUMBER_FIELD_NUMBER: _ClassVar[int]
    MAX_ATTEMPTS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_ERROR_FIELD_NUMBER: _ClassVar[int]
    DELAY_MS_FIELD_NUMBER: _ClassVar[int]
    RETRY_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    attempt_number: int
    max_attempts: int
    timestamp: _common_pb2.Timestamp
    previous_error: _common_pb2.Error
    delay_ms: int
    retry_strategy: str
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., attempt_number: _Optional[int] = ..., max_attempts: _Optional[int] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., previous_error: _Optional[_Union[_common_pb2.Error, _Mapping]] = ..., delay_ms: _Optional[int] = ..., retry_strategy: _Optional[str] = ...) -> None: ...

class TaskTimeout(_message.Message):
    __slots__ = ("task_id", "agent_id", "timestamp", "timeout_seconds", "actual_duration_ms", "last_status", "will_retry")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    LAST_STATUS_FIELD_NUMBER: _ClassVar[int]
    WILL_RETRY_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    timestamp: _common_pb2.Timestamp
    timeout_seconds: int
    actual_duration_ms: int
    last_status: str
    will_retry: bool
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., timeout_seconds: _Optional[int] = ..., actual_duration_ms: _Optional[int] = ..., last_status: _Optional[str] = ..., will_retry: bool = ...) -> None: ...

class TaskResourceAllocated(_message.Message):
    __slots__ = ("task_id", "agent_id", "allocated", "requested", "timestamp", "allocation_id", "queue_position", "queue_time_ms")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ALLOCATED_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ALLOCATION_ID_FIELD_NUMBER: _ClassVar[int]
    QUEUE_POSITION_FIELD_NUMBER: _ClassVar[int]
    QUEUE_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    agent_id: str
    allocated: _common_pb2.ResourceRequirements
    requested: _common_pb2.ResourceRequirements
    timestamp: _common_pb2.Timestamp
    allocation_id: str
    queue_position: int
    queue_time_ms: int
    def __init__(self, task_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., allocated: _Optional[_Union[_common_pb2.ResourceRequirements, _Mapping]] = ..., requested: _Optional[_Union[_common_pb2.ResourceRequirements, _Mapping]] = ..., timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ..., allocation_id: _Optional[str] = ..., queue_position: _Optional[int] = ..., queue_time_ms: _Optional[int] = ...) -> None: ...
