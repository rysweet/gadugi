# Event Router V2 Documentation Index

## 📚 Complete Documentation Guide

This index provides a comprehensive overview of all Event Router V2 documentation and where to find specific information.

## Core Documentation Files

### 1. **README.md** (Main Documentation)
**Location**: `/README.md`

**Contents**:
- ✅ Feature overview and capabilities
- ✅ Quick start guide
- ✅ Installation instructions
- ✅ Basic usage examples
- ✅ Client SDK usage
- ✅ Management CLI commands
- ✅ Event response patterns
- ✅ Testing instructions
- ✅ Configuration options
- ✅ Deployment guidelines
- ✅ API reference
- ✅ Troubleshooting guide
- ✅ Performance metrics
- ✅ Roadmap and future enhancements

### 2. **SUMMARY.md** (Implementation Summary)
**Location**: `/SUMMARY.md`

**Contents**:
- ✅ What was built (complete feature list)
- ✅ Quick start commands
- ✅ Key features explained
- ✅ Testing results
- ✅ Architecture overview
- ✅ Files created
- ✅ Next steps and optional enhancements

### 3. **AGENT_EVENT_MAPPINGS.md** (Event Flow Documentation)
**Location**: `/docs/AGENT_EVENT_MAPPINGS.md`

**Contents**:
- ✅ Event types and purposes
- ✅ Agent lifecycle events
- ✅ Task lifecycle events
- ✅ Workflow events
- ✅ System events
- ✅ Which agents emit which events
- ✅ Which agents consume which events
- ✅ Event flow diagrams
- ✅ Subscription patterns
- ✅ Event priority guidelines
- ✅ Best practices for event naming
- ✅ Testing event flows
- ✅ Monitoring and debugging

### 4. **EVENT_RESPONSE_GUIDE.md** (How to Respond to Events)
**Location**: `/docs/EVENT_RESPONSE_GUIDE.md`

**Contents**:
- ✅ Quick start for event responses
- ✅ Response patterns (7 different patterns)
- ✅ Direct topic responses
- ✅ Wildcard pattern matching
- ✅ Priority-based responses
- ✅ Conditional responses
- ✅ Response chains
- ✅ Stateful responses
- ✅ Aggregation responses
- ✅ Real-world agent examples
- ✅ Best practices
- ✅ Testing event responses
- ✅ Common patterns summary

## Agent Documentation

### 5. **EventRouterManager.md** (Management Agent)
**Location**: `/.claude/agents/EventRouterManager.md`

**Contents**:
- ✅ Agent responsibilities
- ✅ Service management capabilities
- ✅ Configuration management
- ✅ Health monitoring
- ✅ Troubleshooting procedures
- ✅ Standard procedures
- ✅ Integration points
- ✅ Success metrics
- ✅ Example usage

## Source Code Files

### Core System
- **`src/core/router.py`** - Main event router service with WebSocket server
- **`src/core/models.py`** - Event, subscription, and metadata models
- **`src/core/queue.py`** - Priority queue and multi-queue implementations
- **`src/client/client.py`** - Client SDK with auto-reconnection

### Management Tools
- **`manage_router.py`** - CLI for managing the Event Router service
- **`start_server.py`** - Standalone server starter script

## Example Files

### Test Files
- **`test_event_router.py`** - End-to-end test demonstrating all features

### Example Applications
- **`examples/simple_responder.py`** - Basic event response patterns
- **`examples/event_responder_demo.py`** - Complex multi-agent responses
- **`examples/agent_communication.py`** - Full agent communication demo
- **`examples/start_server.py`** - Simple server starter
- **`examples/test_client.py`** - Basic client test

## Configuration Files

### Generated Files
- **`router_config.json`** - Router configuration (auto-created)
- **`event_router.pid`** - Process ID file (when running as daemon)
- **`event_router.log`** - Service logs
- **`_start_router.py`** - Auto-generated daemon script

## Key Features Documentation

### 🔧 Management
- **Starting/Stopping**: See `manage_router.py` usage in README
- **Configuration**: Interactive via `manage_router.py configure`
- **Monitoring**: Real-time via `manage_router.py monitor`
- **Agent Control**: Via `/agent:EventRouterManager`

### 📡 Event Handling
- **Publishing Events**: See Client SDK section in README
- **Subscribing**: See subscription patterns in README
- **Response Patterns**: Complete guide in EVENT_RESPONSE_GUIDE.md
- **Event Types**: Full list in AGENT_EVENT_MAPPINGS.md

### 🚀 Deployment
- **Local Development**: Zero dependencies, works out of the box
- **Daemon Mode**: `manage_router.py start --daemon`
- **Docker**: Dockerfile example in README
- **Cloud Ready**: Pluggable transport layer design

### 🔍 Troubleshooting
- **Connection Issues**: See Troubleshooting section in README
- **Event Not Received**: Check subscription topics and priorities
- **Memory Issues**: Enable multi-queue mode
- **Port Conflicts**: Use `lsof -i:9090` to check

## Testing Documentation

### Test Coverage
- ✅ WebSocket connection establishment
- ✅ Event publishing and delivery
- ✅ Topic-based subscriptions
- ✅ Priority processing
- ✅ Auto-reconnection
- ✅ Health monitoring
- ✅ Management CLI operations
- ✅ Multi-agent communication

### Running Tests
```bash
# Basic test
uv run python test_event_router.py

# All examples
uv run python examples/simple_responder.py
uv run python examples/event_responder_demo.py
uv run python examples/agent_communication.py
```

## Architecture Documentation

### System Architecture
```
Event Router V2
├── WebSocket Server (handles connections)
├── Event Queue (priority-based)
├── Event Processor (delivers events)
├── Subscription Manager (tracks subscriptions)
└── Health Monitor (metrics and status)
```

### Event Flow
1. Client publishes event via WebSocket
2. Event added to priority queue
3. Processor retrieves event by priority
4. Event matched against subscriptions
5. Event delivered to matching subscribers

## API Documentation

### Client SDK API
- `connect()` - Connect to router
- `disconnect()` - Disconnect from router
- `publish(topic, payload, priority)` - Publish event
- `subscribe(topics, callback)` - Subscribe to events
- `@client.on(pattern)` - Decorator for handlers
- `get_health()` - Get router health

### Management CLI API
- `start [--daemon]` - Start service
- `stop` - Stop service
- `restart` - Restart service
- `status` - Check status
- `configure` - Interactive config
- `monitor` - Watch events
- `logs [-n N] [-f]` - View logs

## Best Practices Documentation

### Event Naming
- Use dot notation: `category.action`
- Be specific: `task.review.completed`
- Use past tense for completed actions

### Priority Guidelines
- CRITICAL: System failures, security
- HIGH: Important business events
- NORMAL: Regular operations
- LOW: Logging, metrics

### Performance Optimization
- Use specific topics over wildcards
- Enable multi-queue for high volume
- Monitor queue depth regularly
- Clean up unused subscriptions

## Getting Help

### Documentation Navigation
1. **New Users**: Start with README.md Quick Start
2. **Developers**: See EVENT_RESPONSE_GUIDE.md for patterns
3. **Operators**: Use manage_router.py and agent docs
4. **Architects**: Review AGENT_EVENT_MAPPINGS.md for system design

### Common Tasks
- **Start Router**: `uv run python manage_router.py start --daemon`
- **Check Health**: `uv run python manage_router.py status`
- **Monitor Events**: `uv run python manage_router.py monitor`
- **Test Connection**: `uv run python test_event_router.py`
- **Respond to Events**: See EVENT_RESPONSE_GUIDE.md

### Support Resources
- **Agent Help**: `/agent:EventRouterManager`
- **Logs**: `event_router.log`
- **Config**: `router_config.json`
- **Examples**: `/examples/` directory

## Summary

The Event Router V2 documentation provides comprehensive coverage of:
- ✅ Installation and setup
- ✅ Configuration and management
- ✅ Event publishing and subscribing
- ✅ Response patterns and examples
- ✅ Agent communication patterns
- ✅ Testing and troubleshooting
- ✅ Architecture and design
- ✅ Best practices and guidelines

All documentation is designed to be practical, with working examples and clear explanations to help users quickly adopt and effectively use the Event Router V2 system.
