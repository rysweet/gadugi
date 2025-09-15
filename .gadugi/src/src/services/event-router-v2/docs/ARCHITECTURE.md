# Event Router V2 - Architecture Document

## System Architecture Overview

The Event Router V2 is designed as a modular, layered system that can scale from a simple in-process message bus to a distributed event streaming platform.

## Architectural Principles

### 1. Separation of Concerns
Each layer has a single, well-defined responsibility:
- **Transport Layer**: Communication protocol handling
- **Core Engine**: Event routing and processing logic
- **Persistence Layer**: Data storage and recovery
- **Client Layer**: Developer-facing API

### 2. Dependency Inversion
- Core components depend on abstractions, not implementations
- Transport and persistence are pluggable
- Easy to test with mocks/stubs

### 3. Event-Driven Architecture
- Everything is an event
- Loose coupling between components
- Asynchronous by default

### 4. Fail-Safe Defaults
- Graceful degradation
- Automatic recovery
- Safe fallback modes

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (Agents, Services, Workflows using Event Router)           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Client SDK Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   API    │  │ Reconnect│  │  Cache   │  │  Builder │  │
│  │  Facade  │  │  Manager │  │  Manager │  │  Pattern │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Transport Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Memory  │  │WebSocket │  │  Redis   │  │  Kafka   │  │
│  │Transport │  │Transport │  │Transport │  │Transport │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Core Engine Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Router  │  │  Queue   │  │  Filter  │  │Dispatcher│  │
│  │  Engine  │  │  Manager │  │  Engine  │  │  Engine  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Persistence Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  SQLite  │  │  Redis   │  │    S3    │  │ PostgreSQL│  │
│  │  Store   │  │  Cache   │  │  Archive │  │   Store  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Health  │  │  Metrics │  │  Logging │  │  Tracing │  │
│  │  Checks  │  │  Export  │  │  System  │  │  System  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Core Engine Components

#### 1. Router Engine

```python
class RouterEngine:
    """Central routing logic."""

    def __init__(self):
        self.routes: Dict[str, List[Subscription]] = {}
        self.patterns: List[PatternRoute] = []
        self.filters: List[GlobalFilter] = []

    async def route(self, event: Event) -> List[Subscriber]:
        """Determine which subscribers should receive an event."""

        # Step 1: Find direct topic matches
        subscribers = self._match_direct_routes(event)

        # Step 2: Find pattern matches
        subscribers.extend(self._match_patterns(event))

        # Step 3: Apply global filters
        subscribers = self._apply_filters(event, subscribers)

        # Step 4: Remove duplicates
        return list(set(subscribers))

    def _match_direct_routes(self, event: Event) -> List[Subscriber]:
        """Match event to direct topic subscriptions."""
        topic = event.type
        return self.routes.get(topic, [])

    def _match_patterns(self, event: Event) -> List[Subscriber]:
        """Match event to pattern subscriptions."""
        matches = []
        for pattern_route in self.patterns:
            if pattern_route.matches(event):
                matches.extend(pattern_route.subscribers)
        return matches
```

#### 2. Queue Manager

```python
class QueueManager:
    """Priority queue management with overflow handling."""

    def __init__(self, max_size: int = 10000):
        self.queues: List[asyncio.PriorityQueue] = [
            asyncio.PriorityQueue() for _ in range(10)  # 10 priority levels
        ]
        self.max_size = max_size
        self.current_size = 0
        self.overflow_policy = OverflowPolicy.DROP_OLDEST

    async def enqueue(self, event: Event) -> bool:
        """Add event to appropriate priority queue."""

        # Check capacity
        if self.current_size >= self.max_size:
            if not await self._handle_overflow():
                return False

        # Add to priority queue
        priority = event.priority
        queue = self.queues[priority]
        await queue.put((event.timestamp, event))
        self.current_size += 1

        return True

    async def dequeue(self) -> Optional[Event]:
        """Get next event from highest priority non-empty queue."""

        # Check queues from highest to lowest priority
        for queue in reversed(self.queues):
            if not queue.empty():
                _, event = await queue.get()
                self.current_size -= 1
                return event

        return None

    async def _handle_overflow(self) -> bool:
        """Handle queue overflow based on policy."""

        if self.overflow_policy == OverflowPolicy.DROP_OLDEST:
            # Drop oldest event from lowest priority queue
            for queue in self.queues:
                if not queue.empty():
                    await queue.get()
                    self.current_size -= 1
                    return True

        elif self.overflow_policy == OverflowPolicy.DROP_NEWEST:
            # Reject new event
            return False

        elif self.overflow_policy == OverflowPolicy.BLOCK:
            # Wait for space
            while self.current_size >= self.max_size:
                await asyncio.sleep(0.01)
            return True

        return False
```

#### 3. Filter Engine

```python
class FilterEngine:
    """Advanced event filtering with multiple strategies."""

    def __init__(self):
        self.filters: List[Filter] = []
        self.compiled_filters: Dict[str, CompiledFilter] = {}

    def add_filter(self, filter_spec: Dict[str, Any]) -> str:
        """Add a new filter and return its ID."""

        # Compile filter for performance
        compiled = self._compile_filter(filter_spec)
        filter_id = str(uuid4())
        self.compiled_filters[filter_id] = compiled

        return filter_id

    def match(self, event: Event, filter_id: str) -> bool:
        """Check if event matches filter."""

        compiled_filter = self.compiled_filters.get(filter_id)
        if not compiled_filter:
            return False

        return compiled_filter.match(event)

    def _compile_filter(self, spec: Dict[str, Any]) -> CompiledFilter:
        """Compile filter specification for fast matching."""

        # Parse filter spec
        conditions = []

        for field, criteria in spec.items():
            if isinstance(criteria, dict):
                # Complex criteria like {"$gt": 100}
                for op, value in criteria.items():
                    conditions.append(
                        Condition(field, Operator(op), value)
                    )
            else:
                # Simple equality
                conditions.append(
                    Condition(field, Operator.EQUALS, criteria)
                )

        return CompiledFilter(conditions)

class CompiledFilter:
    """Pre-compiled filter for fast evaluation."""

    def __init__(self, conditions: List[Condition]):
        self.conditions = conditions
        self.field_accessors = self._build_accessors()

    def match(self, event: Event) -> bool:
        """Check if event matches all conditions."""

        for condition in self.conditions:
            accessor = self.field_accessors[condition.field]
            value = accessor(event)

            if not condition.evaluate(value):
                return False

        return True

    def _build_accessors(self) -> Dict[str, Callable]:
        """Build fast field accessors."""

        accessors = {}
        for condition in self.conditions:
            # Create optimized accessor for nested fields
            field_path = condition.field.split('.')
            accessor = lambda e, path=field_path: self._get_nested(e, path)
            accessors[condition.field] = accessor

        return accessors
```

#### 4. Dispatcher Engine

```python
class DispatcherEngine:
    """Handles event delivery to subscribers."""

    def __init__(self, worker_count: int = 4):
        self.workers = []
        self.dispatch_queue = asyncio.Queue()
        self.retry_queue = asyncio.Queue()
        self.dead_letter_queue = []

        # Start worker tasks
        for _ in range(worker_count):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)

    async def dispatch(self, event: Event, subscribers: List[Subscriber]):
        """Queue event for delivery to subscribers."""

        for subscriber in subscribers:
            dispatch_task = DispatchTask(event, subscriber)
            await self.dispatch_queue.put(dispatch_task)

    async def _worker(self):
        """Worker task that delivers events."""

        while True:
            try:
                # Get next dispatch task
                task = await self.dispatch_queue.get()

                # Attempt delivery
                success = await self._deliver(task)

                if not success:
                    # Handle delivery failure
                    await self._handle_failure(task)

            except Exception as e:
                logger.error(f"Worker error: {e}")

    async def _deliver(self, task: DispatchTask) -> bool:
        """Deliver event to subscriber."""

        try:
            # Apply timeout
            await asyncio.wait_for(
                task.subscriber.handler(task.event),
                timeout=task.subscriber.timeout
            )
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Delivery timeout for {task.subscriber.id}")
            return False

        except Exception as e:
            logger.error(f"Delivery error: {e}")
            return False

    async def _handle_failure(self, task: DispatchTask):
        """Handle delivery failure with retry logic."""

        task.attempts += 1

        if task.attempts < task.max_attempts:
            # Schedule retry with backoff
            delay = self._calculate_backoff(task.attempts)
            await asyncio.sleep(delay)
            await self.retry_queue.put(task)
        else:
            # Send to dead letter queue
            self.dead_letter_queue.append(task)
            await self._persist_dead_letter(task)
```

### Transport Layer Architecture

#### Abstract Transport Interface

```python
class Transport(ABC):
    """Abstract base class for all transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish transport connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close transport connection."""
        pass

    @abstractmethod
    async def send(self, data: bytes) -> None:
        """Send data through transport."""
        pass

    @abstractmethod
    async def receive(self) -> bytes:
        """Receive data from transport."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        pass
```

#### Memory Transport (Local Development)

```python
class MemoryTransport(Transport):
    """In-memory transport for local development."""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.subscribers: Dict[str, asyncio.Queue] = {}
        self.connected = False

    async def connect(self) -> None:
        """No actual connection needed."""
        self.connected = True

    async def send(self, data: bytes) -> None:
        """Put data in memory queue."""

        # Deserialize to route to subscribers
        event = self._deserialize(data)

        # Send to all matching subscribers
        for sub_id, sub_queue in self.subscribers.items():
            if self._matches_subscription(event, sub_id):
                await sub_queue.put(data)

    async def receive(self) -> bytes:
        """Get data from memory queue."""
        return await self.queue.get()
```

#### WebSocket Transport

```python
class WebSocketTransport(Transport):
    """WebSocket transport for real-time communication."""

    def __init__(self, url: str):
        self.url = url
        self.websocket = None
        self.reconnector = AutoReconnector(self)

    async def connect(self) -> None:
        """Establish WebSocket connection."""

        try:
            self.websocket = await websockets.connect(
                self.url,
                ping_interval=30,
                ping_timeout=10
            )

            # Start heartbeat task
            asyncio.create_task(self._heartbeat())

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self.url}")

    async def send(self, data: bytes) -> None:
        """Send data through WebSocket."""

        if not self.is_connected():
            await self.reconnector.reconnect()

        try:
            await self.websocket.send(data)
        except websockets.ConnectionClosed:
            await self.reconnector.reconnect()
            await self.websocket.send(data)

    async def _heartbeat(self):
        """Send periodic ping to keep connection alive."""

        while self.is_connected():
            try:
                pong = await self.websocket.ping()
                await asyncio.wait_for(pong, timeout=10)
                await asyncio.sleep(30)
            except:
                # Connection lost, trigger reconnect
                await self.reconnector.reconnect()
```

#### Redis Transport

```python
class RedisTransport(Transport):
    """Redis transport for distributed systems."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.redis = None
        self.pubsub = None

    async def connect(self) -> None:
        """Connect to Redis."""

        self.redis = await aioredis.create_redis_pool(
            f'redis://{self.host}:{self.port}',
            minsize=5,
            maxsize=10
        )

        self.pubsub = self.redis.pubsub()

    async def send(self, data: bytes) -> None:
        """Publish to Redis channel."""

        event = self._deserialize(data)
        channel = f"events:{event.type}"

        await self.redis.publish(channel, data)

    async def receive(self) -> bytes:
        """Receive from Redis subscription."""

        message = await self.pubsub.get_message(
            ignore_subscribe_messages=True,
            timeout=1.0
        )

        if message and message['type'] == 'message':
            return message['data']

        return None
```

### Persistence Layer Architecture

#### Abstract Persistence Interface

```python
class PersistenceStore(ABC):
    """Abstract base for persistence stores."""

    @abstractmethod
    async def save(self, event: Event) -> None:
        """Persist an event."""
        pass

    @abstractmethod
    async def load(self, event_id: str) -> Optional[Event]:
        """Load an event by ID."""
        pass

    @abstractmethod
    async def query(self, criteria: Dict) -> List[Event]:
        """Query events by criteria."""
        pass

    @abstractmethod
    async def delete(self, event_id: str) -> None:
        """Delete an event."""
        pass
```

#### SQLite Persistence

```python
class SQLitePersistence(PersistenceStore):
    """SQLite persistence for local development."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    async def initialize(self):
        """Initialize database schema."""

        self.conn = await aiosqlite.connect(self.db_path)

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                priority INTEGER,
                timestamp REAL,
                source TEXT,
                target TEXT,
                payload TEXT,
                metadata TEXT,
                correlation_id TEXT,
                created_at REAL DEFAULT (datetime('now'))
            )
        ''')

        # Create indexes
        await self.conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_type ON events(type)'
        )
        await self.conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)'
        )
        await self.conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_correlation ON events(correlation_id)'
        )

        await self.conn.commit()

    async def save(self, event: Event) -> None:
        """Save event to SQLite."""

        await self.conn.execute('''
            INSERT INTO events (
                id, type, priority, timestamp, source, target,
                payload, metadata, correlation_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.id,
            event.type,
            event.priority,
            event.timestamp.timestamp(),
            event.source,
            event.target,
            json.dumps(event.payload),
            json.dumps(event.metadata),
            event.correlation_id
        ))

        await self.conn.commit()
```

### Client SDK Architecture

#### SDK Core

```python
class EventRouterClient:
    """Main client SDK class."""

    def __init__(self, config: Optional[Dict] = None):
        # Load configuration
        self.config = self._load_config(config)

        # Create transport
        self.transport = TransportFactory.create(self.config)

        # Create connection manager
        self.connection = ConnectionManager(self.transport)

        # Create subscription manager
        self.subscriptions = SubscriptionManager()

        # Create cache
        self.cache = EventCache(self.config.get('cache', {}))

        # Start background tasks
        self._start_background_tasks()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Connect to event router."""
        await self.connection.connect()

    async def disconnect(self):
        """Disconnect from event router."""
        await self.connection.disconnect()

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        **kwargs
    ) -> str:
        """Publish an event."""

        # Create event
        event = Event(
            type=event_type,
            payload=payload,
            source=self.config.get('client_id'),
            timestamp=datetime.utcnow(),
            **kwargs
        )

        # Check cache for deduplication
        if self.cache.contains(event):
            return event.id

        # Send through transport
        await self.transport.send(event.to_bytes())

        # Add to cache
        self.cache.add(event)

        return event.id
```

#### Auto-Reconnection

```python
class AutoReconnector:
    """Handles automatic reconnection with exponential backoff."""

    def __init__(self, transport: Transport):
        self.transport = transport
        self.reconnecting = False
        self.attempt = 0
        self.max_attempts = 10
        self.base_delay = 1.0
        self.max_delay = 60.0

    async def reconnect(self):
        """Attempt to reconnect with backoff."""

        if self.reconnecting:
            return  # Already reconnecting

        self.reconnecting = True

        while self.attempt < self.max_attempts:
            try:
                # Calculate backoff delay
                delay = min(
                    self.base_delay * (2 ** self.attempt),
                    self.max_delay
                )

                # Add jitter
                delay += random.uniform(0, delay * 0.1)

                logger.info(f"Reconnecting in {delay:.1f}s (attempt {self.attempt + 1})")
                await asyncio.sleep(delay)

                # Attempt reconnection
                await self.transport.connect()

                # Success!
                logger.info("Reconnected successfully")
                self.attempt = 0
                self.reconnecting = False
                return

            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
                self.attempt += 1

        # Max attempts exceeded
        logger.error("Max reconnection attempts exceeded")
        self.reconnecting = False
        raise ConnectionError("Failed to reconnect after maximum attempts")
```

## Data Flow Architecture

### Event Publishing Flow

```
Client publishes event
        │
        ▼
[Client SDK Layer]
  - Validate event
  - Add metadata
  - Check cache
        │
        ▼
[Transport Layer]
  - Serialize event
  - Send to router
        │
        ▼
[Core Engine Layer]
  - Receive event
  - Enqueue by priority
        │
        ▼
[Queue Manager]
  - Priority queuing
  - Overflow handling
        │
        ▼
[Router Engine]
  - Match subscriptions
  - Apply filters
        │
        ▼
[Dispatcher Engine]
  - Deliver to subscribers
  - Handle retries
        │
        ▼
[Persistence Layer]
  - Save event
  - Update indexes
```

### Event Subscription Flow

```
Client subscribes to topics
        │
        ▼
[Client SDK Layer]
  - Register handler
  - Create subscription
        │
        ▼
[Transport Layer]
  - Send subscription
  - Maintain connection
        │
        ▼
[Core Engine Layer]
  - Register subscription
  - Update routing table
        │
        ▼
[Events arrive]
        │
        ▼
[Router Engine]
  - Match to subscription
  - Check filters
        │
        ▼
[Dispatcher Engine]
  - Queue for delivery
  - Worker processes
        │
        ▼
[Transport Layer]
  - Send to client
        │
        ▼
[Client SDK Layer]
  - Deserialize event
  - Call handler
```

## Scaling Architecture

### Vertical Scaling

- Increase worker threads
- Larger queue sizes
- More memory for caching
- Faster disk for persistence

### Horizontal Scaling

```
      Load Balancer
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
Router1  Router2  Router3
    │      │      │
    └──────┼──────┘
           ▼
     Shared Redis
```

### Partitioning Strategy

```python
class PartitionedRouter:
    """Distributes events across multiple routers."""

    def __init__(self, partitions: int):
        self.partitions = partitions
        self.routers = [RouterEngine() for _ in range(partitions)]

    def get_partition(self, event: Event) -> int:
        """Determine partition for event."""

        # Use consistent hashing
        hash_value = hashlib.md5(
            event.correlation_id.encode()
        ).hexdigest()

        return int(hash_value, 16) % self.partitions

    async def route(self, event: Event):
        """Route event to correct partition."""

        partition = self.get_partition(event)
        router = self.routers[partition]

        return await router.route(event)
```

## Monitoring Architecture

### Health Check System

```python
class HealthChecker:
    """Comprehensive health checking."""

    async def check_health(self) -> HealthStatus:
        """Run all health checks."""

        checks = {
            'transport': await self._check_transport(),
            'persistence': await self._check_persistence(),
            'queue': await self._check_queue(),
            'workers': await self._check_workers()
        }

        overall = all(c.is_healthy for c in checks.values())

        return HealthStatus(
            is_healthy=overall,
            checks=checks,
            timestamp=datetime.utcnow()
        )

    async def _check_transport(self) -> CheckResult:
        """Check transport health."""

        try:
            # Test connection
            await self.transport.ping()
            return CheckResult(
                is_healthy=True,
                message="Transport connected"
            )
        except Exception as e:
            return CheckResult(
                is_healthy=False,
                message=f"Transport error: {e}"
            )
```

### Metrics Collection

```python
class MetricsCollector:
    """Collects and exports metrics."""

    def __init__(self):
        self.counters = {}
        self.gauges = {}
        self.histograms = {}

    def increment(self, metric: str, value: int = 1):
        """Increment a counter."""

        if metric not in self.counters:
            self.counters[metric] = 0

        self.counters[metric] += value

    def record_latency(self, operation: str, duration: float):
        """Record operation latency."""

        if operation not in self.histograms:
            self.histograms[operation] = []

        self.histograms[operation].append(duration)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""

        lines = []

        # Export counters
        for name, value in self.counters.items():
            lines.append(f"event_router_{name}_total {value}")

        # Export gauges
        for name, value in self.gauges.items():
            lines.append(f"event_router_{name} {value}")

        # Export histograms
        for name, values in self.histograms.items():
            if values:
                lines.append(f"event_router_{name}_p50 {np.percentile(values, 50)}")
                lines.append(f"event_router_{name}_p95 {np.percentile(values, 95)}")
                lines.append(f"event_router_{name}_p99 {np.percentile(values, 99)}")

        return '\n'.join(lines)
```

## Security Architecture

### Authentication Layer

```python
class AuthenticationManager:
    """Handles client authentication."""

    def __init__(self):
        self.providers = {
            'api_key': ApiKeyAuthProvider(),
            'jwt': JwtAuthProvider(),
            'mtls': MtlsAuthProvider()
        }

    async def authenticate(self, credentials: Dict) -> AuthContext:
        """Authenticate client."""

        auth_type = credentials.get('type')
        provider = self.providers.get(auth_type)

        if not provider:
            raise AuthenticationError(f"Unknown auth type: {auth_type}")

        return await provider.authenticate(credentials)
```

### Authorization Layer

```python
class AuthorizationManager:
    """Handles permission checks."""

    def __init__(self):
        self.policies = {}

    def can_publish(self, context: AuthContext, event: Event) -> bool:
        """Check if client can publish event."""

        # Check topic permissions
        if not self._has_topic_permission(context, event.type, 'publish'):
            return False

        # Check rate limits
        if not self._check_rate_limit(context, 'publish'):
            return False

        return True

    def can_subscribe(self, context: AuthContext, topics: List[str]) -> bool:
        """Check if client can subscribe to topics."""

        for topic in topics:
            if not self._has_topic_permission(context, topic, 'subscribe'):
                return False

        return True
```

This architecture provides a robust, scalable foundation for the Event Router V2 that can grow from local development to distributed production deployments.
