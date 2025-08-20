# Event Router Requirements

## Functional Requirements

### Core Messaging
- The service MUST provide async pub/sub messaging between agents
- The service SHALL support topic-based routing of events
- The service MUST handle protobuf-encoded events
- The service SHALL spawn agent processes when needed
- The service MUST maintain a dead letter queue for failed events

### Process Management
- The service MUST spawn agents as subprocesses
- The service SHALL monitor agent health via heartbeats
- The service MUST restart failed agents automatically
- The service SHALL isolate agent processes from each other
- The service MUST clean up zombie processes

### Event Types
- The service MUST handle AgentStarted events
- The service MUST handle AgentStopped events
- The service MUST handle HasQuestion events for interactive Q&A
- The service MUST handle NeedsApproval events for critical decisions only (NOT for normal development tasks)
- The service SHALL support custom event types via protobuf

### Routing and Filtering
- The service MUST route events based on topic patterns
- The service SHALL support wildcard subscriptions
- The service MUST filter events by namespace
- The service SHALL support priority-based routing
- The service MUST maintain event ordering per topic

## Non-Functional Requirements

### Performance
- Response time must be under 10ms for event routing
- Service should handle 10,000 events/second
- Dead letter queue should persist for 7 days
- Memory usage should not exceed 500MB

### Reliability
- Service must have 99.9% uptime
- Events must not be lost during crashes
- Service must recover from restart within 5 seconds
- Failed events must be retried 3 times

### Observability
- Service must log all event routing decisions
- Service must expose Prometheus metrics
- Service must track event latency
- Service must report queue depths