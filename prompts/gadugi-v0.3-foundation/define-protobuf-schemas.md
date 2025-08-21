# Define Protobuf Schemas Task

## Objective
Create comprehensive protobuf definitions for Gadugi v0.3 event system in `.claude/protos/` directory with Python bindings.

## Requirements

### Directory Structure
Create the following structure:
```
.claude/
└── protos/
    ├── agent_events.proto
    ├── task_events.proto
    ├── common.proto
    └── generated/
        └── python/
            ├── agent_events_pb2.py
            ├── task_events_pb2.py
            └── common_pb2.py
```

### 1. Common Types (common.proto)
Define shared message types:
```protobuf
syntax = "proto3";
package gadugi.common;

message Timestamp {
  int64 seconds = 1;
  int32 nanos = 2;
}

message Metadata {
  map<string, string> labels = 1;
  map<string, string> annotations = 2;
}

enum Priority {
  PRIORITY_UNSPECIFIED = 0;
  PRIORITY_LOW = 1;
  PRIORITY_NORMAL = 2;
  PRIORITY_HIGH = 3;
  PRIORITY_CRITICAL = 4;
}

message Error {
  string code = 1;
  string message = 2;
  string details = 3;
  string stack_trace = 4;
}
```

### 2. Agent Events (agent_events.proto)
Define agent-specific events:
```protobuf
syntax = "proto3";
package gadugi.agent;

import "common.proto";

message AgentStarted {
  string agent_id = 1;
  string agent_type = 2;
  common.Timestamp timestamp = 3;
  common.Metadata metadata = 4;
  string version = 5;
  repeated string capabilities = 6;
}

message AgentStopped {
  string agent_id = 1;
  common.Timestamp timestamp = 2;
  string reason = 3;
  int32 exit_code = 4;
  common.Error error = 5;
}

message AgentHasQuestion {
  string agent_id = 1;
  string question_id = 2;
  string question = 3;
  repeated string options = 4;
  common.Priority priority = 5;
  common.Timestamp timestamp = 6;
  int32 timeout_seconds = 7;
}

message AgentNeedsApproval {
  string agent_id = 1;
  string approval_id = 2;
  string action = 3;
  string description = 4;
  map<string, string> parameters = 5;
  common.Priority priority = 6;
  common.Timestamp timestamp = 7;
  repeated string approvers = 8;
}

message AgentResponse {
  string agent_id = 1;
  string request_id = 2;
  oneof response {
    string answer = 3;
    bool approval = 4;
    common.Error error = 5;
  }
  common.Timestamp timestamp = 6;
  common.Metadata metadata = 7;
}

message AgentHeartbeat {
  string agent_id = 1;
  common.Timestamp timestamp = 2;
  string status = 3;
  map<string, double> metrics = 4;
}
```

### 3. Task Events (task_events.proto)
Define task-specific events:
```protobuf
syntax = "proto3";
package gadugi.task;

import "common.proto";

message TaskStarted {
  string task_id = 1;
  string parent_task_id = 2;
  string agent_id = 3;
  string task_type = 4;
  string description = 5;
  common.Timestamp timestamp = 6;
  common.Priority priority = 7;
  map<string, string> parameters = 8;
  common.Metadata metadata = 9;
}

message TaskProgress {
  string task_id = 1;
  string agent_id = 2;
  int32 percent_complete = 3;
  string status_message = 4;
  common.Timestamp timestamp = 5;
  repeated string completed_steps = 6;
  repeated string remaining_steps = 7;
}

message TaskCompleted {
  string task_id = 1;
  string agent_id = 2;
  common.Timestamp timestamp = 3;
  oneof result {
    string success_message = 4;
    bytes output_data = 5;
  }
  map<string, string> outputs = 6;
  int64 duration_ms = 7;
  common.Metadata metadata = 8;
}

message TaskFailed {
  string task_id = 1;
  string agent_id = 2;
  common.Timestamp timestamp = 3;
  common.Error error = 4;
  bool retriable = 5;
  int32 retry_count = 6;
  string recovery_suggestion = 7;
}

message TaskDependency {
  string task_id = 1;
  repeated string depends_on = 2;
  repeated string blocks = 3;
}

message TaskCancelled {
  string task_id = 1;
  string agent_id = 2;
  string reason = 3;
  common.Timestamp timestamp = 4;
  string cancelled_by = 5;
}
```

### 4. Python Bindings Generation
- Install protobuf compiler: `uv add protobuf grpcio-tools`
- Create generation script `generate_protos.py`:
```python
#!/usr/bin/env python3
"""Generate Python bindings from protobuf definitions."""

import subprocess
from pathlib import Path

def generate_python_bindings():
    proto_dir = Path(".claude/protos")
    output_dir = proto_dir / "generated" / "python"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    proto_files = proto_dir.glob("*.proto")
    
    for proto_file in proto_files:
        cmd = [
            "python", "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_file)
        ]
        subprocess.run(cmd, check=True)
        print(f"Generated bindings for {proto_file.name}")

if __name__ == "__main__":
    generate_python_bindings()
```

### 5. Python Usage Examples
Create `examples/use_protos.py`:
```python
"""Example usage of protobuf messages."""

from pathlib import Path
import sys

# Add generated protos to path
sys.path.append(str(Path(".claude/protos/generated/python")))

import agent_events_pb2
import task_events_pb2
import common_pb2

# Create an agent started event
agent_started = agent_events_pb2.AgentStarted()
agent_started.agent_id = "agent-123"
agent_started.agent_type = "WorkflowManager"
agent_started.version = "0.3.0"
agent_started.capabilities.extend(["task_execution", "parallel_processing"])

# Create a task progress event
task_progress = task_events_pb2.TaskProgress()
task_progress.task_id = "task-456"
task_progress.agent_id = "agent-123"
task_progress.percent_complete = 75
task_progress.status_message = "Processing step 3 of 4"

# Serialize and deserialize
serialized = agent_started.SerializeToString()
deserialized = agent_events_pb2.AgentStarted()
deserialized.ParseFromString(serialized)
```

## Success Criteria
- All protobuf files created with comprehensive message definitions
- Python bindings successfully generated
- No compilation errors
- Example usage code works correctly
- All event types covered
- Proper imports and dependencies between proto files
- Documentation for each message type

## Implementation Notes
- Use proto3 syntax for modern compatibility
- Include comprehensive field documentation
- Design for extensibility
- Consider backward compatibility
- Test serialization/deserialization
- Ensure UV environment compatibility