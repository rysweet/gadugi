import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
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

class AgentStarted(_message.Message):
    __slots__ = (
        "agent_id",
        "agent_type",
        "agent_name",
        "timestamp",
        "metadata",
        "version",
        "capabilities",
        "resources",
        "parent_agent_id",
        "config",
    )
    class ConfigEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    AGENT_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    CAPABILITIES_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    PARENT_AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    agent_type: str
    agent_name: str
    timestamp: _common_pb2.Timestamp
    metadata: _common_pb2.Metadata
    version: str
    capabilities: _containers.RepeatedScalarFieldContainer[str]
    resources: _common_pb2.ResourceRequirements
    parent_agent_id: str
    config: _containers.ScalarMap[str, str]
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        agent_type: _Optional[str] = ...,
        agent_name: _Optional[str] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        metadata: _Optional[_Union[_common_pb2.Metadata, _Mapping]] = ...,
        version: _Optional[str] = ...,
        capabilities: _Optional[_Iterable[str]] = ...,
        resources: _Optional[_Union[_common_pb2.ResourceRequirements, _Mapping]] = ...,
        parent_agent_id: _Optional[str] = ...,
        config: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class AgentStopped(_message.Message):
    __slots__ = (
        "agent_id",
        "timestamp",
        "reason",
        "exit_code",
        "error",
        "runtime_ms",
        "final_metrics",
        "will_restart",
    )
    class FinalMetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[float] = ...
        ) -> None: ...

    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_MS_FIELD_NUMBER: _ClassVar[int]
    FINAL_METRICS_FIELD_NUMBER: _ClassVar[int]
    WILL_RESTART_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    timestamp: _common_pb2.Timestamp
    reason: str
    exit_code: int
    error: _common_pb2.Error
    runtime_ms: int
    final_metrics: _containers.ScalarMap[str, float]
    will_restart: bool
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        reason: _Optional[str] = ...,
        exit_code: _Optional[int] = ...,
        error: _Optional[_Union[_common_pb2.Error, _Mapping]] = ...,
        runtime_ms: _Optional[int] = ...,
        final_metrics: _Optional[_Mapping[str, float]] = ...,
        will_restart: bool = ...,
    ) -> None: ...

class AgentHasQuestion(_message.Message):
    __slots__ = (
        "agent_id",
        "question_id",
        "question",
        "options",
        "priority",
        "timestamp",
        "timeout_seconds",
        "context",
        "requires_confirmation",
        "default_answer",
    )
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    QUESTION_ID_FIELD_NUMBER: _ClassVar[int]
    QUESTION_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    REQUIRES_CONFIRMATION_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_ANSWER_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    question_id: str
    question: str
    options: _containers.RepeatedScalarFieldContainer[str]
    priority: _common_pb2.Priority
    timestamp: _common_pb2.Timestamp
    timeout_seconds: int
    context: str
    requires_confirmation: bool
    default_answer: str
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        question_id: _Optional[str] = ...,
        question: _Optional[str] = ...,
        options: _Optional[_Iterable[str]] = ...,
        priority: _Optional[_Union[_common_pb2.Priority, str]] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        timeout_seconds: _Optional[int] = ...,
        context: _Optional[str] = ...,
        requires_confirmation: bool = ...,
        default_answer: _Optional[str] = ...,
    ) -> None: ...

class AgentNeedsApproval(_message.Message):
    __slots__ = (
        "agent_id",
        "approval_id",
        "action",
        "description",
        "parameters",
        "priority",
        "timestamp",
        "approvers",
        "timeout_seconds",
        "risk_level",
        "impacts",
        "auto_approve_on_timeout",
    )
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    APPROVAL_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    APPROVERS_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    RISK_LEVEL_FIELD_NUMBER: _ClassVar[int]
    IMPACTS_FIELD_NUMBER: _ClassVar[int]
    AUTO_APPROVE_ON_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    approval_id: str
    action: str
    description: str
    parameters: _containers.ScalarMap[str, str]
    priority: _common_pb2.Priority
    timestamp: _common_pb2.Timestamp
    approvers: _containers.RepeatedScalarFieldContainer[str]
    timeout_seconds: int
    risk_level: str
    impacts: _containers.RepeatedScalarFieldContainer[str]
    auto_approve_on_timeout: bool
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        approval_id: _Optional[str] = ...,
        action: _Optional[str] = ...,
        description: _Optional[str] = ...,
        parameters: _Optional[_Mapping[str, str]] = ...,
        priority: _Optional[_Union[_common_pb2.Priority, str]] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        approvers: _Optional[_Iterable[str]] = ...,
        timeout_seconds: _Optional[int] = ...,
        risk_level: _Optional[str] = ...,
        impacts: _Optional[_Iterable[str]] = ...,
        auto_approve_on_timeout: bool = ...,
    ) -> None: ...

class AgentResponse(_message.Message):
    __slots__ = (
        "agent_id",
        "request_id",
        "answer",
        "approval",
        "error",
        "timestamp",
        "metadata",
        "responder_id",
        "justification",
    )
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    ANSWER_FIELD_NUMBER: _ClassVar[int]
    APPROVAL_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    RESPONDER_ID_FIELD_NUMBER: _ClassVar[int]
    JUSTIFICATION_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    request_id: str
    answer: str
    approval: bool
    error: _common_pb2.Error
    timestamp: _common_pb2.Timestamp
    metadata: _common_pb2.Metadata
    responder_id: str
    justification: str
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        request_id: _Optional[str] = ...,
        answer: _Optional[str] = ...,
        approval: bool = ...,
        error: _Optional[_Union[_common_pb2.Error, _Mapping]] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        metadata: _Optional[_Union[_common_pb2.Metadata, _Mapping]] = ...,
        responder_id: _Optional[str] = ...,
        justification: _Optional[str] = ...,
    ) -> None: ...

class AgentHeartbeat(_message.Message):
    __slots__ = (
        "agent_id",
        "timestamp",
        "status",
        "metrics",
        "memory_usage_mb",
        "cpu_usage_percent",
        "active_tasks",
        "queued_tasks",
        "health_status",
        "warnings",
    )
    class MetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[float] = ...
        ) -> None: ...

    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_MB_FIELD_NUMBER: _ClassVar[int]
    CPU_USAGE_PERCENT_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_TASKS_FIELD_NUMBER: _ClassVar[int]
    QUEUED_TASKS_FIELD_NUMBER: _ClassVar[int]
    HEALTH_STATUS_FIELD_NUMBER: _ClassVar[int]
    WARNINGS_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    timestamp: _common_pb2.Timestamp
    status: _common_pb2.AgentStatus
    metrics: _containers.ScalarMap[str, float]
    memory_usage_mb: int
    cpu_usage_percent: float
    active_tasks: int
    queued_tasks: int
    health_status: str
    warnings: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        status: _Optional[_Union[_common_pb2.AgentStatus, str]] = ...,
        metrics: _Optional[_Mapping[str, float]] = ...,
        memory_usage_mb: _Optional[int] = ...,
        cpu_usage_percent: _Optional[float] = ...,
        active_tasks: _Optional[int] = ...,
        queued_tasks: _Optional[int] = ...,
        health_status: _Optional[str] = ...,
        warnings: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class AgentStateChanged(_message.Message):
    __slots__ = (
        "agent_id",
        "previous_status",
        "new_status",
        "timestamp",
        "reason",
        "triggered_by",
    )
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_STATUS_FIELD_NUMBER: _ClassVar[int]
    NEW_STATUS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    TRIGGERED_BY_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    previous_status: _common_pb2.AgentStatus
    new_status: _common_pb2.AgentStatus
    timestamp: _common_pb2.Timestamp
    reason: str
    triggered_by: str
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        previous_status: _Optional[_Union[_common_pb2.AgentStatus, str]] = ...,
        new_status: _Optional[_Union[_common_pb2.AgentStatus, str]] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        reason: _Optional[str] = ...,
        triggered_by: _Optional[str] = ...,
    ) -> None: ...

class AgentCapabilityRegistered(_message.Message):
    __slots__ = (
        "agent_id",
        "capability_name",
        "capability_version",
        "description",
        "dependencies",
        "timestamp",
        "parameters",
    )
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    CAPABILITY_NAME_FIELD_NUMBER: _ClassVar[int]
    CAPABILITY_VERSION_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    capability_name: str
    capability_version: str
    description: str
    dependencies: _containers.RepeatedScalarFieldContainer[str]
    timestamp: _common_pb2.Timestamp
    parameters: _containers.ScalarMap[str, str]
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        capability_name: _Optional[str] = ...,
        capability_version: _Optional[str] = ...,
        description: _Optional[str] = ...,
        dependencies: _Optional[_Iterable[str]] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        parameters: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class AgentMessage(_message.Message):
    __slots__ = (
        "from_agent_id",
        "to_agent_id",
        "message_id",
        "message_type",
        "payload",
        "priority",
        "timestamp",
        "correlation_id",
        "requires_response",
        "timeout_seconds",
    )
    FROM_AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TO_AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    CORRELATION_ID_FIELD_NUMBER: _ClassVar[int]
    REQUIRES_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    from_agent_id: str
    to_agent_id: str
    message_id: str
    message_type: str
    payload: bytes
    priority: _common_pb2.Priority
    timestamp: _common_pb2.Timestamp
    correlation_id: str
    requires_response: bool
    timeout_seconds: int
    def __init__(
        self,
        from_agent_id: _Optional[str] = ...,
        to_agent_id: _Optional[str] = ...,
        message_id: _Optional[str] = ...,
        message_type: _Optional[str] = ...,
        payload: _Optional[bytes] = ...,
        priority: _Optional[_Union[_common_pb2.Priority, str]] = ...,
        timestamp: _Optional[_Union[_common_pb2.Timestamp, _Mapping]] = ...,
        correlation_id: _Optional[str] = ...,
        requires_response: bool = ...,
        timeout_seconds: _Optional[int] = ...,
    ) -> None: ...
