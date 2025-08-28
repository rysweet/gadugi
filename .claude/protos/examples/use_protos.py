#!/usr/bin/env python3
"""Example usage of Gadugi v0.3 protobuf messages."""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add generated protos to path
sys.path.append(str(Path(__file__).parent.parent / "generated" / "python"))

try:
    # Import generated protobuf modules
    import agent_events_pb2  # type: ignore[import]
    import task_events_pb2  # type: ignore[import]
    import common_pb2  # type: ignore[import]
except ImportError:
    print("ERROR: Protobuf bindings not generated yet.")
    print("Run: python .claude/protos/generate_protos.py")
    sys.exit(1)


def create_timestamp() -> common_pb2.Timestamp:
    """Create a protobuf timestamp for current time."""
    now = time.time()
    timestamp = common_pb2.Timestamp()
    timestamp.seconds = int(now)
    timestamp.nanos = int((now - int(now)) * 1e9)
    return timestamp


def example_agent_started():
    """Example of creating an AgentStarted event."""
    print("\n1. Creating AgentStarted event...")
    
    event = agent_events_pb2.AgentStarted()
    event.agent_id = "agent-123"
    event.agent_type = "WorkflowManager"
    event.agent_name = "Primary Workflow Manager"
    event.timestamp.CopyFrom(create_timestamp())
    event.version = "0.3.0"
    event.capabilities.extend(["task_execution", "parallel_processing", "state_management"])
    
    # Set resource requirements
    event.resources.cpu_cores = 2.0
    event.resources.memory_mb = 1024
    event.resources.disk_mb = 5120
    
    # Add metadata
    event.metadata.labels["environment"] = "production"
    event.metadata.labels["region"] = "us-west-2"
    event.metadata.annotations["team"] = "platform"
    
    # Add configuration
    event.config["max_parallel_tasks"] = "10"
    event.config["heartbeat_interval"] = "30"
    
    print(f"  Agent ID: {event.agent_id}")
    print(f"  Agent Type: {event.agent_type}")
    print(f"  Capabilities: {list(event.capabilities)}")
    print(f"  Resources: CPU={event.resources.cpu_cores}, Memory={event.resources.memory_mb}MB")
    
    # Serialize and show size
    serialized = event.SerializeToString()
    print(f"  Serialized size: {len(serialized)} bytes")
    
    return event


def example_task_started():
    """Example of creating a TaskStarted event."""
    print("\n2. Creating TaskStarted event...")
    
    event = task_events_pb2.TaskStarted()
    event.task_id = "task-456"
    event.workflow_id = "workflow-789"
    event.agent_id = "agent-123"
    event.task_type = "code_review"
    event.task_name = "Review Pull Request #42"
    event.description = "Automated code review for feature branch"
    event.timestamp.CopyFrom(create_timestamp())
    event.priority = common_pb2.PRIORITY_HIGH
    event.timeout_seconds = 300
    
    # Add parameters
    event.parameters["pr_number"] = "42"
    event.parameters["branch"] = "feature/new-capability"
    event.parameters["repository"] = "gadugi/gadugi"
    
    # Add dependencies
    event.dependencies.extend(["task-001", "task-002"])
    
    # Set resource requirements
    event.resources.cpu_cores = 1.0
    event.resources.memory_mb = 512
    
    print(f"  Task ID: {event.task_id}")
    print(f"  Task Type: {event.task_type}")
    print(f"  Priority: {common_pb2.Priority.Name(event.priority)}")
    print(f"  Parameters: {dict(event.parameters)}")
    print(f"  Dependencies: {list(event.dependencies)}")
    
    return event


def example_task_progress():
    """Example of creating a TaskProgress event."""
    print("\n3. Creating TaskProgress event...")
    
    event = task_events_pb2.TaskProgress()
    event.task_id = "task-456"
    event.agent_id = "agent-123"
    event.percent_complete = 75
    event.status_message = "Processing file 3 of 4"
    event.timestamp.CopyFrom(create_timestamp())
    event.elapsed_ms = 45000
    event.estimated_remaining_ms = 15000
    event.current_phase = "analysis"
    
    # Add completed and remaining steps
    event.completed_steps.extend(["initialization", "validation", "preprocessing"])
    event.remaining_steps.extend(["analysis", "report_generation"])
    
    # Add metrics
    event.metrics["files_processed"] = 3.0
    event.metrics["lines_analyzed"] = 1250.0
    event.metrics["issues_found"] = 7.0
    
    print(f"  Task ID: {event.task_id}")
    print(f"  Progress: {event.percent_complete}%")
    print(f"  Status: {event.status_message}")
    print(f"  Completed Steps: {list(event.completed_steps)}")
    print(f"  Metrics: {dict(event.metrics)}")
    
    return event


def example_agent_has_question():
    """Example of creating an AgentHasQuestion event."""
    print("\n4. Creating AgentHasQuestion event...")
    
    event = agent_events_pb2.AgentHasQuestion()
    event.agent_id = "agent-123"
    event.question_id = "q-001"
    event.question = "Multiple implementation approaches found. Which should I use?"
    event.options.extend(["Functional approach", "Object-oriented approach", "Hybrid approach"])
    event.priority = common_pb2.PRIORITY_NORMAL
    event.timestamp.CopyFrom(create_timestamp())
    event.timeout_seconds = 60
    event.context = "Implementing new feature for data processing pipeline"
    event.default_answer = "Functional approach"
    
    print(f"  Agent ID: {event.agent_id}")
    print(f"  Question: {event.question}")
    print(f"  Options: {list(event.options)}")
    print(f"  Default: {event.default_answer}")
    print(f"  Timeout: {event.timeout_seconds}s")
    
    return event


def example_task_completed():
    """Example of creating a TaskCompleted event."""
    print("\n5. Creating TaskCompleted event...")
    
    event = task_events_pb2.TaskCompleted()
    event.task_id = "task-456"
    event.agent_id = "agent-123"
    event.timestamp.CopyFrom(create_timestamp())
    event.success_message = "Code review completed successfully"
    event.duration_ms = 60000
    event.retry_count = 0
    
    # Add outputs
    event.outputs["review_status"] = "approved"
    event.outputs["issues_found"] = "7"
    event.outputs["suggestions_made"] = "3"
    
    # Add performance metrics
    event.performance_metrics["throughput"] = 125.5
    event.performance_metrics["accuracy"] = 0.95
    event.performance_metrics["efficiency"] = 0.88
    
    # Add artifacts
    event.artifacts.extend([
        "/tmp/review-report.md",
        "/tmp/metrics.json",
        "/tmp/suggestions.txt"
    ])
    
    print(f"  Task ID: {event.task_id}")
    print(f"  Status: {event.success_message}")
    print(f"  Duration: {event.duration_ms}ms")
    print(f"  Outputs: {dict(event.outputs)}")
    print(f"  Artifacts: {list(event.artifacts)}")
    
    return event


def example_serialization():
    """Example of serialization and deserialization."""
    print("\n6. Testing serialization/deserialization...")
    
    # Create an event
    original = agent_events_pb2.AgentStarted()
    original.agent_id = "test-agent"
    original.agent_type = "TestAgent"
    original.version = "0.3.0"
    
    # Serialize to bytes
    serialized = original.SerializeToString()
    print(f"  Serialized size: {len(serialized)} bytes")
    
    # Deserialize back
    deserialized = agent_events_pb2.AgentStarted()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.agent_id == original.agent_id
    assert deserialized.agent_type == original.agent_type
    assert deserialized.version == original.version
    print(f"  ✓ Deserialization successful")
    print(f"  Agent ID: {deserialized.agent_id}")
    print(f"  Agent Type: {deserialized.agent_type}")
    
    return deserialized


def main():
    """Run all examples."""
    print("=" * 60)
    print("Gadugi v0.3 Protobuf Examples")
    print("=" * 60)
    
    try:
        # Run examples
        agent_started = example_agent_started()
        task_started = example_task_started()
        task_progress = example_task_progress()
        agent_question = example_agent_has_question()
        task_completed = example_task_completed()
        deserialized = example_serialization()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()