# Event Router V2 - Production-Ready Implementation Plan

## Executive Summary

A complete redesign of the Gadugi Event Router to create a production-ready, scalable event-driven communication system that works seamlessly from local development to distributed cloud deployments.

## Core Design Principles

1. **Zero External Dependencies for Local Development**: Works out-of-the-box with Python stdlib + minimal deps
2. **Progressive Enhancement**: Scales from in-memory to Redis to Kafka as needed
3. **Developer Experience First**: Simple API, automatic reconnection, clear error messages
4. **Production Ready**: Monitoring, persistence, recovery, and observability built-in
5. **Transport Agnostic**: Same API whether using memory, WebSocket, or Redis

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Event Router V2                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Client     │  │   Client     │  │   Client     │     │
│  │   SDK        │  │   SDK        │  │   SDK        │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼──────┐     │
│  │            Transport Abstraction Layer             │     │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐        │     │
│  │  │ Memory  │  │WebSocket │  │  Redis   │        │     │
│  │  └─────────┘  └──────────┘  └──────────┘        │     │
│  └────────────────────────┬───────────────────────────┘     │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────┐     │
│  │              Core Event Router Engine              │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │     │
│  │  │  Queue   │  │  Filter  │  │  Router  │       │     │
│  │  │  Manager │  │  Engine  │  │  Engine  │       │     │
│  │  └──────────┘  └──────────┘  └──────────┘       │     │
│  └────────────────────────┬───────────────────────────┘     │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────┐     │
│  │            Persistence & Recovery Layer            │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │     │
│  │  │  SQLite  │  │  Redis   │  │   S3     │       │     │
│  │  └──────────┘  └──────────┘  └──────────┘       │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │           Management & Monitoring Layer            │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │     │
│  │  │  Health  │  │  Metrics │  │   CLI    │       │     │
│  │  │  Check   │  │  Export  │  │   Tool   │       │     │
│  │  └──────────┘  └──────────┘  └──────────┘       │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
.claude/services/event-router-v2/
├── docs/
│   ├── API_REFERENCE.md          # Complete API documentation
│   ├── ARCHITECTURE.md           # Detailed architecture docs
│   ├── DEPLOYMENT_GUIDE.md       # Deployment instructions
│   ├── MIGRATION_GUIDE.md        # Migration from v1
│   └── TROUBLESHOOTING.md        # Common issues and solutions
│
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── engine.py             # Core event routing engine
│   │   ├── queue.py              # Priority queue implementation
│   │   ├── filter.py             # Event filtering engine
│   │   ├── router.py             # Routing logic
│   │   └── models.py             # Core data models
│   │
│   ├── transport/
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract transport interface
│   │   ├── memory.py             # In-memory transport (local dev)
│   │   ├── websocket.py          # WebSocket transport
│   │   ├── redis.py              # Redis transport (production)
│   │   └── factory.py            # Transport factory
│   │
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract persistence interface
│   │   ├── sqlite.py             # SQLite for local persistence
│   │   ├── redis.py              # Redis for distributed cache
│   │   ├── s3.py                 # S3 for long-term storage
│   │   └── manager.py            # Persistence orchestration
│   │
│   ├── client/
│   │   ├── __init__.py
│   │   ├── sdk.py                # Main client SDK
│   │   ├── connection.py         # Connection management
│   │   ├── reconnect.py          # Auto-reconnection logic
│   │   └── builder.py            # Fluent API builder
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── health.py             # Health checks
│   │   ├── metrics.py            # Metrics collection
│   │   ├── logging.py            # Structured logging
│   │   └── tracing.py            # Distributed tracing
│   │
│   └── management/
│       ├── __init__.py
│       ├── cli.py                # CLI tool
│       ├── agent.py              # Management agent
│       └── api.py                # Management API
│
├── tests/
│   ├── unit/
│   │   ├── test_engine.py
│   │   ├── test_queue.py
│   │   ├── test_filter.py
│   │   └── test_transport.py
│   │
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   ├── test_persistence.py
│   │   └── test_reconnection.py
│   │
│   └── performance/
│       ├── test_throughput.py
│       └── test_latency.py
│
├── examples/
│   ├── simple_publisher.py       # Basic publishing example
│   ├── simple_subscriber.py      # Basic subscription example
│   ├── agent_integration.py      # Agent integration example
│   ├── distributed_workflow.py   # Distributed workflow example
│   └── monitoring_dashboard.py   # Monitoring example
│
├── config/
│   ├── default.yaml              # Default configuration
│   ├── development.yaml          # Development settings
│   ├── production.yaml           # Production settings
│   └── schema.json               # Configuration schema
│
├── scripts/
│   ├── install.sh                # Installation script
│   ├── start.sh                  # Start script
│   ├── health_check.sh           # Health check script
│   └── benchmark.py              # Performance benchmark
│
├── pyproject.toml                # Project configuration
├── README.md                     # Main documentation
├── LICENSE                       # License file
└── CHANGELOG.md                  # Version history
```

## Core Components Design

### 1. Event Model (Enhanced)

```python
@dataclass
class Event:
    """Enhanced event model with full traceability."""
    
    # Core fields
    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Routing fields
    source: str = ""
    target: Optional[str] = None
    topic: Optional[str] = None
    
    # Metadata fields
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    # Priority and TTL
    priority: int = 5  # 1-10, higher is more important
    ttl: Optional[int] = None  # Time to live in seconds
    expires_at: Optional[datetime] = None
    
    # Delivery tracking
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    
    # Audit fields
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
```

### 2. Transport Abstraction

```python
class Transport(ABC):
    """Abstract transport interface."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass
    
    @abstractmethod
    async def publish(self, event: Event) -> str:
        """Publish an event."""
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Event], Awaitable[None]]
    ) -> str:
        """Subscribe to topics."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from topics."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        pass
```

### 3. Client SDK API

```python
class EventRouterClient:
    """Simple, developer-friendly client SDK."""
    
    def __init__(self, url: str = "localhost:8080", transport: str = "auto"):
        """Initialize client with auto-detection."""
        self.transport = TransportFactory.create(url, transport)
        self.reconnector = AutoReconnector(self.transport)
        
    async def publish(self, event_type: str, payload: Dict, **kwargs) -> str:
        """Publish an event with simple API."""
        event = Event(
            type=event_type,
            payload=payload,
            **kwargs
        )
        return await self.transport.publish(event)
    
    async def subscribe(self, *topics, handler=None) -> Subscription:
        """Subscribe to topics with decorator support."""
        if handler:
            return await self.transport.subscribe(topics, handler)
        
        # Decorator style
        def decorator(func):
            asyncio.create_task(
                self.transport.subscribe(topics, func)
            )
            return func
        return decorator
    
    def on(self, event_type: str):
        """Decorator for event handlers."""
        def decorator(func):
            asyncio.create_task(
                self.subscribe(event_type, handler=func)
            )
            return func
        return decorator

# Usage examples:
client = EventRouterClient()

# Simple publish
await client.publish("user.created", {"id": 123, "name": "John"})

# Simple subscribe
@client.on("user.created")
async def handle_user_created(event):
    print(f"New user: {event.payload}")

# With filtering
await client.subscribe(
    "order.*",
    handler=lambda e: print(f"Order event: {e}"),
    filter={"priority": {"$gte": 7}}
)
```

### 4. Configuration Schema

```yaml
# config/default.yaml
event_router:
  # Transport settings
  transport:
    type: "auto"  # auto, memory, websocket, redis
    connection:
      host: "localhost"
      port: 8080
      timeout: 30
      retry:
        enabled: true
        max_attempts: 5
        backoff: "exponential"
        
  # Persistence settings
  persistence:
    enabled: true
    type: "sqlite"  # sqlite, redis, s3
    sqlite:
      path: "~/.gadugi/events.db"
      max_size: "100MB"
    retention:
      default: "7d"
      by_type:
        audit: "90d"
        debug: "1d"
        
  # Queue settings
  queue:
    max_size: 10000
    overflow_policy: "drop_oldest"  # drop_oldest, drop_newest, block
    priority_levels: 10
    
  # Performance settings
  performance:
    worker_threads: 4
    batch_size: 100
    flush_interval: "100ms"
    
  # Monitoring settings
  monitoring:
    health_check:
      enabled: true
      port: 8081
      path: "/health"
    metrics:
      enabled: true
      export_interval: "10s"
      exporters:
        - type: "prometheus"
          port: 9090
    logging:
      level: "info"
      format: "json"
      output: "stdout"
```

## Implementation Phases

### Phase 1: Core Event Router (Week 1)
**Goal**: Basic event routing with in-memory transport

**Deliverables**:
1. Core event model and types
2. In-memory transport implementation
3. Basic queue management
4. Simple publish/subscribe API
5. Unit tests for core functionality

**Success Criteria**:
- Can publish and receive events locally
- Priority-based queue works correctly
- Basic filtering works
- 90% test coverage

### Phase 2: Persistence & Recovery (Week 2)
**Goal**: Add persistence and recovery capabilities

**Deliverables**:
1. SQLite persistence layer
2. Event replay functionality
3. Recovery after crash
4. Dead letter queue
5. Integration tests

**Success Criteria**:
- Events persist across restarts
- Can replay events from checkpoint
- Failed events go to DLQ
- Recovery completes < 5 seconds

### Phase 3: Client SDK & Reconnection (Week 3)
**Goal**: Production-ready client SDK

**Deliverables**:
1. Auto-reconnection logic
2. Connection pooling
3. Fluent API builder
4. Circuit breaker pattern
5. Client-side caching

**Success Criteria**:
- Automatic reconnection works
- No message loss during reconnection
- Clean API with good DX
- Comprehensive examples

### Phase 4: Management & CLI (Week 4)
**Goal**: Management tools and observability

**Deliverables**:
1. CLI tool for management
2. Management agent
3. Health check endpoints
4. Metrics collection
5. Monitoring dashboard

**Success Criteria**:
- CLI can manage all aspects
- Health checks are comprehensive
- Metrics exported to Prometheus
- Dashboard shows real-time status

### Phase 5: Production Hardening (Week 5)
**Goal**: Production readiness

**Deliverables**:
1. Performance optimization
2. Security hardening
3. Comprehensive documentation
4. Deployment scripts
5. Load testing

**Success Criteria**:
- Handles 10K events/second
- < 10ms p99 latency
- Secure by default
- Full documentation

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies
- Aim for 90% coverage
- Use property-based testing for edge cases

### Integration Tests
- Test component interactions
- Test persistence and recovery
- Test transport switching
- Test reconnection scenarios

### Performance Tests
- Benchmark throughput (events/second)
- Measure latency (p50, p95, p99)
- Test under load
- Memory leak detection

### Chaos Tests
- Random disconnections
- Network partitions
- Process crashes
- Disk full scenarios

## Migration Path from V1

### Step 1: Compatibility Layer
```python
# Provide compatibility wrapper
from event_router_v2 import EventRouterClient
from event_router_v1 import EventRouter as V1Router

class CompatibilityRouter(V1Router):
    """Wrapper to maintain V1 API compatibility."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.v2_client = EventRouterClient()
    
    async def publish_event(self, event):
        """V1 compatible publish."""
        return await self.v2_client.publish(
            event.type.value,
            event.payload,
            source=event.source,
            target=event.target
        )
```

### Step 2: Gradual Migration
1. Deploy V2 alongside V1
2. Route new services to V2
3. Migrate existing services gradually
4. Monitor both systems
5. Deprecate V1 after full migration

### Step 3: Data Migration
```python
# Migration script
async def migrate_events():
    """Migrate events from V1 to V2."""
    v1_store = V1EventStore()
    v2_store = V2EventStore()
    
    async for event in v1_store.get_all():
        v2_event = convert_v1_to_v2(event)
        await v2_store.save(v2_event)
```

## API Examples

### Publishing Events
```python
# Simple publish
await client.publish("user.created", {"id": 123})

# With options
await client.publish(
    "order.placed",
    {"order_id": 456, "total": 99.99},
    priority=8,
    target="payment_service",
    correlation_id="abc-123"
)

# Batch publish
await client.publish_batch([
    ("metric.cpu", {"value": 75}),
    ("metric.memory", {"value": 2048}),
    ("metric.disk", {"value": 80})
])
```

### Subscribing to Events
```python
# Simple subscription
@client.on("user.*")
async def handle_user_events(event):
    print(f"User event: {event}")

# With filtering
subscription = await client.subscribe(
    "payment.*",
    filter={
        "payload.amount": {"$gt": 100},
        "priority": {"$gte": 7}
    },
    handler=process_high_value_payment
)

# Pattern matching
@client.on_pattern(r"order\.(created|updated|cancelled)")
async def handle_order_lifecycle(event):
    await update_order_status(event)
```

### Request-Response Pattern
```python
# Request with timeout
response = await client.request(
    "service.calculate",
    {"x": 10, "y": 20},
    timeout=5.0
)
print(f"Result: {response.payload['result']}")

# Responding to requests
@client.respond("service.calculate")
async def handle_calculation(request):
    result = request.payload["x"] + request.payload["y"]
    return {"result": result}
```

### Stream Processing
```python
# Process event stream
async for event in client.stream("sensor.*", batch_size=100):
    await process_sensor_data(event)

# Windowed aggregation
async for window in client.window("metric.*", size="1m"):
    avg = sum(e.payload["value"] for e in window) / len(window)
    await client.publish("metric.average", {"value": avg})
```

## Security Considerations

### Authentication
- JWT token support
- API key authentication
- mTLS for production
- OAuth2 integration ready

### Authorization
- Topic-based permissions
- Role-based access control
- Event type filtering
- Rate limiting per client

### Encryption
- TLS for all transports
- Payload encryption option
- End-to-end encryption support
- Key rotation capability

### Audit
- All events logged
- Access audit trail
- Compliance mode (GDPR, HIPAA)
- Tamper-proof event log

## Performance Targets

### Throughput
- Local: 50K events/second
- WebSocket: 10K events/second
- Redis: 100K events/second

### Latency
- p50: < 1ms
- p95: < 5ms
- p99: < 10ms

### Resource Usage
- Memory: < 100MB base
- CPU: < 5% idle
- Disk: Configurable limits

### Scalability
- Horizontal scaling ready
- Partitioning support
- Multi-region capability
- Auto-scaling friendly

## Monitoring & Observability

### Health Checks
```json
GET /health
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "checks": {
    "transport": "connected",
    "persistence": "available",
    "queue": "66% capacity",
    "workers": "4/4 active"
  }
}
```

### Metrics
- Events published/second
- Events delivered/second
- Queue depth by priority
- Error rate by type
- Latency percentiles
- Connection count
- Subscription count

### Logging
- Structured JSON logs
- Correlation ID tracking
- Log levels: DEBUG, INFO, WARN, ERROR
- Log sampling for high volume

### Tracing
- OpenTelemetry support
- Distributed trace context
- Event flow visualization
- Performance bottleneck detection

## Deployment Options

### Local Development
```bash
# Install and start
pip install gadugi-event-router
event-router start --dev
```

### Docker
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -e .
CMD ["event-router", "start"]
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-router
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: event-router
        image: gadugi/event-router:v2
        ports:
        - containerPort: 8080
        env:
        - name: TRANSPORT
          value: "redis"
```

### Cloud Native
- AWS: ECS/EKS + ElastiCache
- GCP: Cloud Run + Memorystore
- Azure: Container Instances + Cache for Redis

## Success Metrics

### Technical Metrics
- Zero message loss
- 99.99% uptime
- < 10ms p99 latency
- 10K+ events/second

### Developer Experience
- 5-minute quickstart
- Clear error messages
- Comprehensive docs
- Active community

### Business Impact
- Reduced coupling
- Faster feature delivery
- Better observability
- Lower operational cost

## Risk Mitigation

### Technical Risks
- **Risk**: Message loss during failures
  **Mitigation**: Persistence, acknowledgments, retries

- **Risk**: Performance degradation at scale
  **Mitigation**: Load testing, monitoring, auto-scaling

- **Risk**: Security vulnerabilities
  **Mitigation**: Security audit, encryption, authentication

### Operational Risks
- **Risk**: Complex deployment
  **Mitigation**: Docker images, Helm charts, documentation

- **Risk**: Debugging difficulties
  **Mitigation**: Comprehensive logging, tracing, monitoring

## Timeline & Milestones

### Week 1: Foundation
- Core implementation
- Basic testing
- Initial documentation

### Week 2: Persistence
- Storage layers
- Recovery mechanisms
- Integration tests

### Week 3: Client SDK
- SDK development
- Auto-reconnection
- Examples

### Week 4: Management
- CLI tool
- Monitoring
- Dashboard

### Week 5: Production
- Performance tuning
- Security hardening
- Final documentation

### Week 6: Launch
- Migration guide
- Training materials
- Community launch

## Conclusion

This implementation plan provides a clear path to building a production-ready event router that:
1. Works seamlessly from local development to cloud scale
2. Provides excellent developer experience
3. Handles failures gracefully
4. Offers comprehensive observability
5. Maintains backward compatibility

The phased approach ensures we deliver value incrementally while building toward a robust, enterprise-ready solution.
