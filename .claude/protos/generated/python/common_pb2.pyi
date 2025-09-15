from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class Priority(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PRIORITY_UNSPECIFIED: _ClassVar[Priority]
    PRIORITY_LOW: _ClassVar[Priority]
    PRIORITY_NORMAL: _ClassVar[Priority]
    PRIORITY_HIGH: _ClassVar[Priority]
    PRIORITY_CRITICAL: _ClassVar[Priority]

class AgentStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AGENT_STATUS_UNSPECIFIED: _ClassVar[AgentStatus]
    AGENT_STATUS_INITIALIZING: _ClassVar[AgentStatus]
    AGENT_STATUS_RUNNING: _ClassVar[AgentStatus]
    AGENT_STATUS_PAUSED: _ClassVar[AgentStatus]
    AGENT_STATUS_STOPPING: _ClassVar[AgentStatus]
    AGENT_STATUS_STOPPED: _ClassVar[AgentStatus]
    AGENT_STATUS_ERROR: _ClassVar[AgentStatus]
    AGENT_STATUS_MAINTENANCE: _ClassVar[AgentStatus]

class TaskStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TASK_STATUS_UNSPECIFIED: _ClassVar[TaskStatus]
    TASK_STATUS_PENDING: _ClassVar[TaskStatus]
    TASK_STATUS_SCHEDULED: _ClassVar[TaskStatus]
    TASK_STATUS_RUNNING: _ClassVar[TaskStatus]
    TASK_STATUS_PAUSED: _ClassVar[TaskStatus]
    TASK_STATUS_COMPLETED: _ClassVar[TaskStatus]
    TASK_STATUS_FAILED: _ClassVar[TaskStatus]
    TASK_STATUS_CANCELLED: _ClassVar[TaskStatus]
    TASK_STATUS_TIMEOUT: _ClassVar[TaskStatus]

PRIORITY_UNSPECIFIED: Priority
PRIORITY_LOW: Priority
PRIORITY_NORMAL: Priority
PRIORITY_HIGH: Priority
PRIORITY_CRITICAL: Priority
AGENT_STATUS_UNSPECIFIED: AgentStatus
AGENT_STATUS_INITIALIZING: AgentStatus
AGENT_STATUS_RUNNING: AgentStatus
AGENT_STATUS_PAUSED: AgentStatus
AGENT_STATUS_STOPPING: AgentStatus
AGENT_STATUS_STOPPED: AgentStatus
AGENT_STATUS_ERROR: AgentStatus
AGENT_STATUS_MAINTENANCE: AgentStatus
TASK_STATUS_UNSPECIFIED: TaskStatus
TASK_STATUS_PENDING: TaskStatus
TASK_STATUS_SCHEDULED: TaskStatus
TASK_STATUS_RUNNING: TaskStatus
TASK_STATUS_PAUSED: TaskStatus
TASK_STATUS_COMPLETED: TaskStatus
TASK_STATUS_FAILED: TaskStatus
TASK_STATUS_CANCELLED: TaskStatus
TASK_STATUS_TIMEOUT: TaskStatus

class Timestamp(_message.Message):
    __slots__ = ("seconds", "nanos")
    SECONDS_FIELD_NUMBER: _ClassVar[int]
    NANOS_FIELD_NUMBER: _ClassVar[int]
    seconds: int
    nanos: int
    def __init__(
        self, seconds: _Optional[int] = ..., nanos: _Optional[int] = ...
    ) -> None: ...

class Metadata(_message.Message):
    __slots__ = ("labels", "annotations", "trace_id", "span_id")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    class AnnotationsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    LABELS_FIELD_NUMBER: _ClassVar[int]
    ANNOTATIONS_FIELD_NUMBER: _ClassVar[int]
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    SPAN_ID_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.ScalarMap[str, str]
    annotations: _containers.ScalarMap[str, str]
    trace_id: str
    span_id: str
    def __init__(
        self,
        labels: _Optional[_Mapping[str, str]] = ...,
        annotations: _Optional[_Mapping[str, str]] = ...,
        trace_id: _Optional[str] = ...,
        span_id: _Optional[str] = ...,
    ) -> None: ...

class Error(_message.Message):
    __slots__ = ("code", "message", "details", "stack_trace", "source", "timestamp")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    STACK_TRACE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    code: str
    message: str
    details: str
    stack_trace: str
    source: str
    timestamp: Timestamp
    def __init__(
        self,
        code: _Optional[str] = ...,
        message: _Optional[str] = ...,
        details: _Optional[str] = ...,
        stack_trace: _Optional[str] = ...,
        source: _Optional[str] = ...,
        timestamp: _Optional[_Union[Timestamp, _Mapping]] = ...,
    ) -> None: ...

class ResourceRequirements(_message.Message):
    __slots__ = (
        "cpu_cores",
        "memory_mb",
        "disk_mb",
        "network_mbps",
        "gpu_count",
        "custom",
    )
    class CustomEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[int] = ...
        ) -> None: ...

    CPU_CORES_FIELD_NUMBER: _ClassVar[int]
    MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    DISK_MB_FIELD_NUMBER: _ClassVar[int]
    NETWORK_MBPS_FIELD_NUMBER: _ClassVar[int]
    GPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_FIELD_NUMBER: _ClassVar[int]
    cpu_cores: float
    memory_mb: int
    disk_mb: int
    network_mbps: int
    gpu_count: int
    custom: _containers.ScalarMap[str, int]
    def __init__(
        self,
        cpu_cores: _Optional[float] = ...,
        memory_mb: _Optional[int] = ...,
        disk_mb: _Optional[int] = ...,
        network_mbps: _Optional[int] = ...,
        gpu_count: _Optional[int] = ...,
        custom: _Optional[_Mapping[str, int]] = ...,
    ) -> None: ...

class RetryPolicy(_message.Message):
    __slots__ = (
        "max_attempts",
        "initial_delay_ms",
        "backoff_multiplier",
        "max_delay_ms",
        "retriable_errors",
    )
    MAX_ATTEMPTS_FIELD_NUMBER: _ClassVar[int]
    INITIAL_DELAY_MS_FIELD_NUMBER: _ClassVar[int]
    BACKOFF_MULTIPLIER_FIELD_NUMBER: _ClassVar[int]
    MAX_DELAY_MS_FIELD_NUMBER: _ClassVar[int]
    RETRIABLE_ERRORS_FIELD_NUMBER: _ClassVar[int]
    max_attempts: int
    initial_delay_ms: int
    backoff_multiplier: float
    max_delay_ms: int
    retriable_errors: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        max_attempts: _Optional[int] = ...,
        initial_delay_ms: _Optional[int] = ...,
        backoff_multiplier: _Optional[float] = ...,
        max_delay_ms: _Optional[int] = ...,
        retriable_errors: _Optional[_Iterable[str]] = ...,
    ) -> None: ...
