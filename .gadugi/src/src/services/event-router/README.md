# Event Router Service - Memory Integration

Enhanced event routing service for Gadugi v0.3 with complete memory system integration, agent lifecycle tracking, event persistence, filtering, and crash recovery capabilities.

## 🚀 Features

### Core Capabilities
- **Agent Lifecycle Tracking**: Complete event tracking for agent initialization, task execution, knowledge learning, and collaboration
- **Memory System Integration**: Seamless integration with Gadugi's v0.3 memory system using SQLite backend
- **Event Persistence**: Reliable storage of events for audit trails and crash recovery
- **Advanced Filtering**: Complex event querying with multiple criteria (type, priority, tags, time ranges)
- **Event Replay**: Complete session replay for crash recovery and debugging
- **Production Ready**: Comprehensive error handling, logging, and monitoring

### Event Types

#### Core System Events (v0.3 Spec)
- `*.started` - Any agent begins task execution (e.g., `orchestration.started`, `workflow.started`)
- `*.stopped` - Any agent completes task execution (e.g., `orchestration.stopped`, `workflow.stopped`)
- `*.hasQuestion` - Agent needs interactive answer from user (high priority)
- `*.needsApproval` - Agent needs user approval for action (high priority)
- `*.cancel` - Cancel another agent's execution (critical priority)

#### Agent Lifecycle Events
- `agent.initialized` - Agent startup and configuration
- `agent.shutdown` - Agent shutdown
- `agent.heartbeat` - Periodic health check

#### Task Events
- `task.started` - Task initiation with dependencies and estimates
- `task.completed` - Task completion with results and metrics
- `task.failed` - Task failures with error details

#### Knowledge & Memory Events
- `knowledge.learned` - Knowledge acquisition and pattern recognition
- `memory.stored` - Memory system storage events
- `memory.recalled` - Memory retrieval events

#### Collaboration Events
- `collaboration.message` - Inter-agent communication and coordination

#### System Events
- `error.occurred` - System errors and exceptions
- `system.health_check` - Health monitoring events
- `system.shutdown` - System shutdown

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flask API     │    │  Event Handler   │    │ Memory Storage  │
│                 │────▶│                  │────▶│                 │
│ • REST Endpoints│    │ • Event Routing  │    │ • SQLite Backend│
│ • Validation    │    │ • Priority Rules │    │ • Memory System │
│ • Error Handling│    │ • Processing     │    │ • Persistence   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │ Filter Engine   │
                       │                 │
                       │ • Complex Queries│
                       │ • Caching       │
                       │ • Pagination    │
                       └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │ Replay Engine   │
                       │                 │
                       │ • Session Recovery│
                       │ • Event Ordering │
                       │ • Time Filtering │
                       └─────────────────┘
```

## 📨 Event Subscriptions

The Event Router implements a pattern-based subscription system that routes events to appropriate agents based on the v0.3 specification.

### Subscription Patterns

Subscriptions support wildcard patterns for flexible event matching:

- `*.started` - Matches any agent's started event
- `*.stopped` - Matches any agent's stopped event
- `workflow.*` - Matches all workflow events
- `orchestration.problem_identified` - Exact event match

### Default Subscriptions (v0.3 Spec)

#### Orchestration Agent
- `*.hasQuestion` → `route_question_to_user` (HIGH priority)
- `*.needsApproval` → `route_approval_to_user` (HIGH priority)
- `*.stopped` → `aggregate_results`
- `decomposition.completed` → `begin_execution_planning`

#### Gadugi Agent
- `*.started` → `track_agent_start`
- `*.stopped` → `track_agent_completion`
- `system.shutdown` → `graceful_shutdown`

#### Team Coach
- `orchestration.stopped` → `trigger_reflection`
- `*.stopped` → `collect_metrics`

#### WorkflowManager
- `orchestration.implementation_started` → `begin_workflow`
- `orchestration.tasks_distributed` → `begin_assigned_workflow`
- `codereview.completed` → `proceed_to_phase_10`

#### Memory Manager
- `*.lessons_learned` → `store_learnings`
- `*.memory_updates` → `update_memories`
- `agent.initialized` → `load_agent_memories`

### Priority Levels

Events are processed based on priority:
1. **CRITICAL** - System failures, cancellations
2. **HIGH** - User interactions (hasQuestion, needsApproval)
3. **NORMAL** - Standard lifecycle events
4. **LOW** - Informational events

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- SQLite3
- Flask
- Pydantic
- aiosqlite
- Access to Gadugi v0.3 memory system

### Installation
```bash
# Clone or navigate to the event-router service directory
cd .claude/services/event-router

# Install dependencies (if using UV)
uv add flask pydantic aiosqlite

# Or using pip
pip install flask pydantic aiosqlite
```

### Configuration
Set environment variables for production:

```bash
# Service Configuration
export EVENT_ROUTER_HOST="0.0.0.0"
export EVENT_ROUTER_PORT="8000"
export EVENT_ROUTER_DEBUG="false"

# Memory System
export EVENT_ROUTER_MEMORY_BACKEND_URL="http://localhost:8000"
export EVENT_ROUTER_SQLITE_DB_PATH="/var/lib/claude/events.db"
export EVENT_ROUTER_ENABLE_MEMORY_INTEGRATION="true"

# Security
export SECRET_KEY="your-production-secret-key"
export EVENT_ROUTER_API_KEY="your-api-key"

# Performance
export EVENT_ROUTER_MAX_EVENT_CACHE_SIZE="1000"
export EVENT_ROUTER_EVENT_RETENTION_DAYS="30"
```

## 🚀 Usage

### Starting the Service
```bash
# Development
python main.py

# Production (with proper configuration)
EVENT_ROUTER_DEBUG=false \
EVENT_ROUTER_SQLITE_DB_PATH="/var/lib/claude/events.db" \
python main.py
```

### API Endpoints

#### Health & Status
```bash
# Health check with memory system status
GET /health

# Detailed service status
GET /status

# Service information
GET /
```

#### Event Management
```bash
# Create a new event
POST /events
Content-Type: application/json
{
    "event_type": "task.started",
    "agent_id": "TaskDecomposer_001",
    "task_id": "task_123",
    "task_description": "Implement feature X",
    "estimated_duration": 60,
    "priority": "high",
    "tags": ["feature", "implementation"]
}

# List events with filtering
GET /events?event_types=task.started,task.completed&limit=50&offset=0

# Advanced filtering
POST /events/filter
Content-Type: application/json
{
    "event_types": ["knowledge.learned"],
    "priority": "high",
    "tags": ["security"],
    "start_time": "2023-01-01T00:00:00Z",
    "limit": 100
}
```

#### Event Replay
```bash
# Replay events for crash recovery
POST /events/replay
Content-Type: application/json
{
    "session_id": "session_123",
    "from_timestamp": "2023-01-01T10:00:00Z",
    "agent_id": "TaskDecomposer_001"
}
```

#### Storage & Memory
```bash
# Get storage statistics
GET /events/storage

# Get memory system integration status
GET /memory/status
```

### Programming Interface

#### Creating Events
```python
from models import TaskStartedEvent, EventPriority

# Create a task started event
event = TaskStartedEvent(
    agent_id="TaskDecomposer_001",
    task_id="task_feature_auth",
    task_description="Implement user authentication",
    estimated_duration=120,
    dependencies=["task_database"],
    priority=EventPriority.HIGH,
    tags=["authentication", "security"]
)

# Send to event router
import requests
response = requests.post(
    "http://localhost:8000/events",
    json=event.dict()
)
```

#### Filtering Events
```python
from models import EventFilter, EventType

# Complex filter
filter_criteria = EventFilter(
    event_types=[EventType.KNOWLEDGE_LEARNED],
    tags=["security"],
    priority=EventPriority.HIGH,
    start_time=datetime.utcnow() - timedelta(hours=24),
    limit=50
)

response = requests.post(
    "http://localhost:8000/events/filter",
    json=filter_criteria.dict()
)
events = response.json()["events"]
```

#### Event Replay
```python
from models import EventReplayRequest

# Replay session for recovery
replay_request = EventReplayRequest(
    session_id="session_crash_recovery",
    from_timestamp=datetime.utcnow() - timedelta(hours=2),
    event_types=[EventType.TASK_STARTED, EventType.TASK_COMPLETED]
)

response = requests.post(
    "http://localhost:8000/events/replay",
    json=replay_request.dict()
)
replay_data = response.json()
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test categories
pytest tests/test_main.py::TestMemoryEventStorage
pytest tests/test_main.py::TestEventReplayEngine
```

### Demo Script
```bash
# Run the comprehensive demo
python demo_event_system.py
```

The demo script demonstrates:
- Complete agent lifecycle event tracking
- Memory system integration
- Event filtering capabilities
- Crash recovery via replay
- Storage system statistics

## 📊 Monitoring & Observability

### Health Checks
The service provides comprehensive health checks:
- Memory system connectivity
- SQLite database status
- Event processing pipeline health
- Cache and performance metrics

### Logging
Structured JSON logging with configurable levels:
```python
# Example log output
{
    "timestamp": "2023-01-01T12:00:00Z",
    "level": "INFO",
    "message": "Event processed successfully",
    "event_id": "evt_123",
    "event_type": "task.started",
    "agent_id": "TaskDecomposer_001",
    "stored_in_memory": true,
    "processing_time_ms": 45
}
```

### Metrics
Key metrics tracked:
- Events processed per minute
- Storage success/failure rates
- Memory integration status
- Filter query performance
- Replay operation statistics

## 🔒 Security

### Authentication
- Optional API key authentication
- Configurable CORS origins
- Request size limits
- Rate limiting (planned)

### Data Protection
- Event data validation
- SQLite connection security
- Memory system access controls
- Audit trail preservation

## 🚀 Production Deployment

### Docker (Planned)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### Environment-Specific Configs
- Development: In-memory SQLite, debug logging
- Testing: Isolated test database, mock memory system
- Production: Persistent storage, structured logging, monitoring

### Scaling Considerations
- SQLite suitable for single-instance deployments
- Memory system integration supports distributed setups
- Event caching optimizes frequent queries
- Configurable retention policies manage storage growth

## 🛣️ Roadmap

### Immediate Enhancements
- [ ] Redis cache integration for high-performance filtering
- [ ] Webhook delivery for real-time event notifications
- [ ] Batch event processing for high-throughput scenarios
- [ ] Advanced analytics and reporting dashboard

### Future Features
- [ ] Event stream processing with Apache Kafka
- [ ] Machine learning for event pattern recognition
- [ ] GraphQL API for complex event queries
- [ ] Multi-tenant event isolation
- [ ] Event encryption for sensitive data

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Set up virtual environment
3. Install development dependencies
4. Run tests to ensure everything works
5. Make changes and add tests
6. Submit pull request

### Code Style
- Follow PEP 8 conventions
- Use type hints throughout
- Add comprehensive docstrings
- Maintain test coverage >90%

## 📚 Related Documentation

- [Gadugi v0.3 Memory System](../memory/README.md)
- [Agent Development Guide](../../agents/README.md)
- [System Architecture Overview](../../README.md)
- [API Reference](./docs/api-reference.md)

## 📄 License

This project is part of the Gadugi system and follows the same licensing terms.

---

**Event Router Service v1.0.0** - Production-ready agent lifecycle event tracking with complete memory system integration for Gadugi v0.3.
