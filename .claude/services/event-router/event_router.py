"""Event Router Service implementation with enhanced features."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .dead_letter_queue import DeadLetterQueue, DeadLetterEntry
from .models import (
    Event,
    EventFilter,
    EventPriority,
    EventStats,
    EventType,
    Subscription,
    SubscriptionType,
)


class EventQueue:
    """Priority-based event queue with batching support."""
    
    def __init__(self, maxsize: int = 10000):
        """Initialize the event queue."""
        self.maxsize = maxsize
        self._queues = {
            EventPriority.CRITICAL: asyncio.Queue(maxsize=maxsize // 4),
            EventPriority.HIGH: asyncio.Queue(maxsize=maxsize // 4),
            EventPriority.NORMAL: asyncio.Queue(maxsize=maxsize // 2),
            EventPriority.LOW: asyncio.Queue(maxsize=maxsize // 4),
        }
        self._total_size = 0
        self._lock = asyncio.Lock()
    
    async def put(self, event: Event) -> None:
        """Add event to queue."""
        async with self._lock:
            if self._total_size >= self.maxsize:
                # Remove oldest low priority event to make space
                try:
                    await asyncio.wait_for(
                        self._queues[EventPriority.LOW].get(),
                        timeout=0.1,
                    )
                    self._total_size -= 1
                except asyncio.TimeoutError:
                    pass
            
            await self._queues[event.priority].put(event)
            self._total_size += 1
    
    async def put_batch(self, events: List[Event]) -> None:
        """Add multiple events to queue."""
        for event in events:
            await self.put(event)
    
    async def get(self, timeout: float = 1.0) -> Optional[Event]:
        """Get next event from queue (priority order)."""
        # Try to get from priority queues in order
        for priority in [
            EventPriority.CRITICAL,
            EventPriority.HIGH,
            EventPriority.NORMAL,
            EventPriority.LOW,
        ]:
            try:
                event = await asyncio.wait_for(
                    self._queues[priority].get(),
                    timeout=0.05,
                )
                async with self._lock:
                    self._total_size -= 1
                return event
            except asyncio.TimeoutError:
                continue
        
        # If no events available immediately, wait for any with timeout
        try:
            tasks = [
                asyncio.create_task(queue.get())
                for queue in self._queues.values()
            ]
            done, pending = await asyncio.wait(
                tasks,
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            if done:
                # Get result from completed task
                result = done.pop().result()
                async with self._lock:
                    self._total_size -= 1
                return result
        except asyncio.TimeoutError:
            pass
        
        return None
    
    async def get_batch(self, max_batch: int = 100, timeout: float = 0.1) -> List[Event]:
        """Get batch of events from queue."""
        batch = []
        deadline = time.time() + timeout
        
        while len(batch) < max_batch and time.time() < deadline:
            remaining_time = deadline - time.time()
            if remaining_time <= 0:
                break
                
            event = await self.get(timeout=remaining_time)
            if event:
                batch.append(event)
            else:
                break
        
        return batch
    
    def qsize(self) -> int:
        """Get total queue size."""
        return self._total_size
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._total_size == 0


class AgentRegistry:
    """Registry for agent discovery and tracking."""
    
    def __init__(self):
        """Initialize the agent registry."""
        self.agents: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def register(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register an agent."""
        async with self._lock:
            self.agents[agent_id] = {
                "id": agent_id,
                "type": agent_type,
                "capabilities": capabilities,
                "metadata": metadata or {},
                "registered_at": datetime.now(),
                "last_heartbeat": datetime.now(),
                "status": "active",
            }
    
    async def unregister(self, agent_id: str) -> None:
        """Unregister an agent."""
        async with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
    
    async def heartbeat(self, agent_id: str) -> None:
        """Update agent heartbeat."""
        async with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id]["last_heartbeat"] = datetime.now()
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information."""
        async with self._lock:
            return self.agents.get(agent_id)
    
    async def find_agents(
        self,
        agent_type: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Find agents by type or capability."""
        async with self._lock:
            results = []
            for agent in self.agents.values():
                if agent_type and agent["type"] != agent_type:
                    continue
                if capability and capability not in agent["capabilities"]:
                    continue
                results.append(agent.copy())
            return results
    
    async def check_health(self, timeout_seconds: int = 60) -> None:
        """Check agent health and mark inactive agents."""
        async with self._lock:
            now = datetime.now()
            for agent_id, agent in self.agents.items():
                last_heartbeat = agent["last_heartbeat"]
                if (now - last_heartbeat).total_seconds() > timeout_seconds:
                    agent["status"] = "inactive"
                else:
                    agent["status"] = "active"


class EventRouterService:
    """Enhanced Event Router Service with all required features."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9090,
        max_workers: int = 10,
        queue_size: int = 10000,
        persistence_path: Optional[Path] = None,
    ):
        """Initialize the event router service."""
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.persistence_path = persistence_path
        
        self.logger = self._setup_logging()
        
        # Core components
        self.event_queue = EventQueue(maxsize=queue_size)
        self.subscriptions: Dict[str, Subscription] = {}
        self.stats = EventStats()
        self.agent_registry = AgentRegistry()
        
        # Dead letter queue for failed deliveries
        self.dead_letter_queue = DeadLetterQueue(
            persistence_path=persistence_path / "dlq" if persistence_path else None,
            auto_retry=True,
            retry_interval=300,  # 5 minutes
        )
        
        # Event replay support
        self.event_history: List[Event] = []
        self.max_history_size = 1000
        self.replay_enabled = True
        
        # Service state
        self.running = False
        self.server_task: Optional[asyncio.Task] = None
        self.processor_tasks: List[asyncio.Task] = []
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Connection management
        self.active_connections: Dict[str, Any] = {}
        
        # Load balancing for subscribers
        self.subscriber_groups: Dict[str, List[str]] = defaultdict(list)
        self.load_balancer_index: Dict[str, int] = defaultdict(int)
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the event router service."""
        logger = logging.getLogger("event_router")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def start(self) -> None:
        """Start the event router service."""
        if self.running:
            self.logger.warning("Event router service is already running")
            return
        
        self.running = True
        self.logger.info(f"Starting event router service on {self.host}:{self.port}")
        
        # Start server task
        self.server_task = asyncio.create_task(self._run_server())
        
        # Start multiple event processor tasks for parallel processing
        for i in range(min(4, self.max_workers)):
            processor_task = asyncio.create_task(self._process_events(worker_id=i))
            self.processor_tasks.append(processor_task)
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Start dead letter queue retry loop
        await self.dead_letter_queue.start_retry_loop(self._retry_event_delivery)
        
        self.logger.info("Event router service started successfully")
    
    async def stop(self) -> None:
        """Stop the event router service."""
        if not self.running:
            return
        
        self.logger.info("Stopping event router service")
        self.running = False
        
        # Stop dead letter queue retry loop
        await self.dead_letter_queue.stop_retry_loop()
        
        # Cancel tasks
        if self.server_task:
            self.server_task.cancel()
        
        for task in self.processor_tasks:
            task.cancel()
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Wait for tasks to complete
        tasks = [self.server_task] + self.processor_tasks + [self.cleanup_task]
        tasks = [task for task in tasks if task]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("Event router service stopped")
    
    async def _run_server(self) -> None:
        """Run the event server."""
        try:
            server = await asyncio.start_server(
                self._handle_client,
                self.host,
                self.port,
            )
            
            self.logger.info(f"Server listening on {self.host}:{self.port}")
            
            async with server:
                await server.serve_forever()
        
        except asyncio.CancelledError:
            self.logger.info("Server task cancelled")
        except Exception as e:
            self.logger.exception(f"Server error: {e}")
    
    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle client connections."""
        client_addr = writer.get_extra_info("peername")
        client_id = f"{client_addr[0]}:{client_addr[1]}:{int(time.time())}"
        
        self.logger.info(f"Client connected: {client_id}")
        self.active_connections[client_id] = {
            "reader": reader,
            "writer": writer,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
        }
        
        try:
            while self.running:
                # Read message length
                length_data = await reader.read(4)
                if not length_data:
                    break
                
                message_length = int.from_bytes(length_data, byteorder="big")
                
                # Read message data
                message_data = await reader.read(message_length)
                if not message_data:
                    break
                
                # Update activity
                self.active_connections[client_id]["last_activity"] = datetime.now()
                
                # Process message
                await self._process_client_message(client_id, message_data)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.exception(f"Error handling client {client_id}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.active_connections.pop(client_id, None)
            self.logger.info(f"Client disconnected: {client_id}")
    
    async def _process_client_message(self, client_id: str, message_data: bytes) -> None:
        """Process message from client."""
        try:
            message = json.loads(message_data.decode("utf-8"))
            message_type = message.get("type", "unknown")
            
            if message_type == "publish_event":
                await self._handle_publish_event(client_id, message)
            elif message_type == "publish_batch":
                await self._handle_publish_batch(client_id, message)
            elif message_type == "subscribe":
                await self._handle_subscription(client_id, message)
            elif message_type == "unsubscribe":
                await self._handle_unsubscription(client_id, message)
            elif message_type == "register_agent":
                await self._handle_agent_registration(client_id, message)
            elif message_type == "agent_heartbeat":
                await self._handle_agent_heartbeat(client_id, message)
            elif message_type == "replay_events":
                await self._handle_replay_request(client_id, message)
            elif message_type == "ping":
                await self._handle_ping(client_id)
            else:
                self.logger.warning(
                    f"Unknown message type from {client_id}: {message_type}",
                )
        
        except Exception as e:
            self.logger.exception(f"Error processing message from {client_id}: {e}")
    
    async def _handle_publish_event(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle event publishing."""
        try:
            event_data = message.get("event", {})
            event = Event.from_dict(event_data)
            
            # Queue event for processing
            await self.publish_event(event)
            
            # Send acknowledgment
            await self._send_to_client(
                client_id,
                {"type": "ack", "event_id": event.id, "status": "queued"},
            )
        
        except Exception as e:
            self.logger.exception(f"Error handling publish event from {client_id}: {e}")
            await self._send_to_client(client_id, {"type": "error", "message": str(e)})
    
    async def _handle_publish_batch(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle batch event publishing."""
        try:
            events_data = message.get("events", [])
            events = [Event.from_dict(data) for data in events_data]
            
            # Queue events for processing
            event_ids = await self.publish_batch(events)
            
            # Send acknowledgment
            await self._send_to_client(
                client_id,
                {"type": "batch_ack", "event_ids": event_ids, "status": "queued"},
            )
        
        except Exception as e:
            self.logger.exception(f"Error handling batch publish from {client_id}: {e}")
            await self._send_to_client(client_id, {"type": "error", "message": str(e)})
    
    async def _handle_subscription(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle subscription request."""
        try:
            sub_data = message.get("subscription", {})
            
            # Create event filter
            filter_data = sub_data.get("filter", {})
            event_filter = EventFilter(
                event_types=[EventType(t) for t in filter_data.get("event_types", [])] if filter_data.get("event_types") else None,
                sources=filter_data.get("sources"),
                targets=filter_data.get("targets"),
                priorities=[EventPriority(p) for p in filter_data.get("priorities", [])] if filter_data.get("priorities") else None,
                pattern=filter_data.get("pattern"),
            )
            
            # Create subscription
            subscription = Subscription(
                id=sub_data.get("id", str(uuid.uuid4())),
                subscriber_id=client_id,
                subscription_type=SubscriptionType(sub_data.get("type", "filtered")),
                filter=event_filter,
                callback=None,
                endpoint=client_id,
            )
            
            self.subscriptions[subscription.id] = subscription
            
            # Add to subscriber group for load balancing
            group_id = sub_data.get("group_id")
            if group_id:
                self.subscriber_groups[group_id].append(subscription.id)
            
            self.logger.info(
                f"Created subscription {subscription.id} for client {client_id}",
            )
            
            # Send acknowledgment
            await self._send_to_client(
                client_id,
                {"type": "subscription_created", "subscription_id": subscription.id},
            )
        
        except Exception as e:
            self.logger.exception(f"Error handling subscription from {client_id}: {e}")
            await self._send_to_client(client_id, {"type": "error", "message": str(e)})
    
    async def _handle_unsubscription(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle unsubscription request."""
        try:
            subscription_id = message.get("subscription_id")
            
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                if subscription.subscriber_id == client_id:
                    del self.subscriptions[subscription_id]
                    
                    # Remove from subscriber groups
                    for group_id, members in self.subscriber_groups.items():
                        if subscription_id in members:
                            members.remove(subscription_id)
                    
                    self.logger.info(
                        f"Removed subscription {subscription_id} for client {client_id}",
                    )
                    
                    await self._send_to_client(
                        client_id,
                        {"type": "unsubscribed", "subscription_id": subscription_id},
                    )
                else:
                    await self._send_to_client(
                        client_id,
                        {"type": "error", "message": "Subscription not owned by client"},
                    )
            else:
                await self._send_to_client(
                    client_id,
                    {"type": "error", "message": "Subscription not found"},
                )
        
        except Exception as e:
            self.logger.exception(f"Error handling unsubscription from {client_id}: {e}")
    
    async def _handle_agent_registration(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle agent registration."""
        try:
            agent_data = message.get("agent", {})
            
            await self.agent_registry.register(
                agent_id=agent_data.get("id", client_id),
                agent_type=agent_data.get("type", "unknown"),
                capabilities=agent_data.get("capabilities", []),
                metadata=agent_data.get("metadata", {}),
            )
            
            await self._send_to_client(
                client_id,
                {"type": "agent_registered", "agent_id": agent_data.get("id", client_id)},
            )
        
        except Exception as e:
            self.logger.exception(f"Error handling agent registration from {client_id}: {e}")
            await self._send_to_client(client_id, {"type": "error", "message": str(e)})
    
    async def _handle_agent_heartbeat(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle agent heartbeat."""
        try:
            agent_id = message.get("agent_id", client_id)
            await self.agent_registry.heartbeat(agent_id)
            
            await self._send_to_client(
                client_id,
                {"type": "heartbeat_ack", "timestamp": datetime.now().isoformat()},
            )
        
        except Exception as e:
            self.logger.exception(f"Error handling agent heartbeat from {client_id}: {e}")
    
    async def _handle_replay_request(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle event replay request."""
        try:
            if not self.replay_enabled:
                await self._send_to_client(
                    client_id,
                    {"type": "error", "message": "Event replay is disabled"},
                )
                return
            
            replay_filter = message.get("filter", {})
            start_time = replay_filter.get("start_time")
            end_time = replay_filter.get("end_time")
            event_types = replay_filter.get("event_types", [])
            
            # Filter events from history
            events_to_replay = []
            for event in self.event_history:
                # Check time range
                if start_time and event.timestamp < datetime.fromisoformat(start_time):
                    continue
                if end_time and event.timestamp > datetime.fromisoformat(end_time):
                    continue
                
                # Check event type
                if event_types and event.type.value not in event_types:
                    continue
                
                events_to_replay.append(event)
            
            # Send replayed events
            for event in events_to_replay:
                await self._send_to_client(
                    client_id,
                    {
                        "type": "replayed_event",
                        "event": event.to_dict(),
                    },
                )
            
            await self._send_to_client(
                client_id,
                {"type": "replay_complete", "count": len(events_to_replay)},
            )
        
        except Exception as e:
            self.logger.exception(f"Error handling replay request from {client_id}: {e}")
            await self._send_to_client(client_id, {"type": "error", "message": str(e)})
    
    async def _handle_ping(self, client_id: str) -> None:
        """Handle ping request."""
        await self._send_to_client(
            client_id,
            {"type": "pong", "timestamp": datetime.now().isoformat()},
        )
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send message to specific client."""
        if client_id not in self.active_connections:
            return
        
        try:
            connection = self.active_connections[client_id]
            writer = connection["writer"]
            
            # Serialize message
            message_data = json.dumps(message).encode("utf-8")
            
            # Send length prefix + message
            length_prefix = len(message_data).to_bytes(4, byteorder="big")
            writer.write(length_prefix + message_data)
            await writer.drain()
        
        except Exception as e:
            self.logger.exception(f"Error sending message to client {client_id}: {e}")
            # Remove client connection on error
            self.active_connections.pop(client_id, None)
    
    async def _process_events(self, worker_id: int) -> None:
        """Process events from the queue."""
        self.logger.info(f"Event processor {worker_id} started")
        
        try:
            while self.running:
                try:
                    # Get batch of events for efficient processing
                    events = await self.event_queue.get_batch(max_batch=50, timeout=1.0)
                    
                    if events:
                        # Process events in parallel
                        tasks = []
                        for event in events:
                            task = asyncio.create_task(self._route_event(event))
                            tasks.append((event, task))
                        
                        # Wait for all routing tasks
                        for event, task in tasks:
                            try:
                                start_time = time.time()
                                await task
                                processing_time = time.time() - start_time
                                
                                # Update stats
                                self.stats.update_from_event(event, processing_time)
                                
                                # Add to history
                                self._add_to_history(event)
                            
                            except Exception as e:
                                self.logger.exception(f"Error processing event {event.id}: {e}")
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.exception(f"Error in event processor {worker_id}: {e}")
        
        except asyncio.CancelledError:
            self.logger.info(f"Event processor {worker_id} cancelled")
    
    async def _route_event(self, event: Event) -> None:
        """Route event to subscribers."""
        matching_subscriptions = self._find_matching_subscriptions(event)
        
        if not matching_subscriptions:
            self.logger.debug(f"No subscribers for event {event.id}")
            return
        
        # Group subscriptions by load balancing group
        grouped_subs = defaultdict(list)
        ungrouped_subs = []
        
        for subscription in matching_subscriptions:
            # Find which group this subscription belongs to
            group_id = None
            for gid, members in self.subscriber_groups.items():
                if subscription.id in members:
                    group_id = gid
                    break
            
            if group_id:
                grouped_subs[group_id].append(subscription)
            else:
                ungrouped_subs.append(subscription)
        
        # Deliver to load-balanced groups (one subscriber per group)
        delivery_tasks = []
        
        for group_id, subs in grouped_subs.items():
            # Round-robin within group
            idx = self.load_balancer_index[group_id] % len(subs)
            self.load_balancer_index[group_id] = idx + 1
            selected_sub = subs[idx]
            
            task = asyncio.create_task(self._deliver_event(event, selected_sub))
            delivery_tasks.append(task)
        
        # Deliver to all ungrouped subscribers
        for subscription in ungrouped_subs:
            task = asyncio.create_task(self._deliver_event(event, subscription))
            delivery_tasks.append(task)
        
        # Wait for all deliveries
        results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
        
        # Count failed deliveries
        failed_count = sum(1 for result in results if isinstance(result, Exception))
        self.stats.failed_deliveries += failed_count
        self.stats.successful_deliveries += len(results) - failed_count
        
        if failed_count > 0:
            self.logger.warning(
                f"Failed to deliver event {event.id} to {failed_count} subscribers",
            )
    
    def _find_matching_subscriptions(self, event: Event) -> List[Subscription]:
        """Find subscriptions that match the event."""
        matching = []
        
        for subscription in self.subscriptions.values():
            if not subscription.is_available():
                continue
            
            if subscription.filter and subscription.filter.matches(event):
                matching.append(subscription)
            elif subscription.subscription_type == SubscriptionType.ALL:
                matching.append(subscription)
        
        return matching
    
    async def _deliver_event(self, event: Event, subscription: Subscription) -> None:
        """Deliver event to subscriber."""
        try:
            if subscription.callback:
                # Direct callback
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    subscription.callback,
                    event,
                )
            elif subscription.endpoint:
                # Send to client endpoint
                await self._send_to_client(
                    subscription.endpoint,
                    {
                        "type": "event",
                        "subscription_id": subscription.id,
                        "event": event.to_dict(),
                    },
                )
            
            # Record successful delivery
            subscription.record_delivery()
        
        except Exception as e:
            self.logger.exception(
                f"Error delivering event {event.id} to subscription {subscription.id}: {e}",
            )
            
            # Record error
            subscription.record_error()
            
            # Add to dead letter queue if circuit breaker is open or max retries reached
            if subscription.circuit_breaker_open or not event.should_retry():
                await self.dead_letter_queue.add(
                    event,
                    e,
                    subscription,
                    permanent_failure=subscription.circuit_breaker_open,
                )
            
            raise
    
    async def _retry_event_delivery(
        self,
        event: Event,
        subscription: Optional[Subscription] = None,
    ) -> None:
        """Retry event delivery from dead letter queue."""
        if subscription:
            # Retry delivery to specific subscription
            await self._deliver_event(event, subscription)
        else:
            # Re-route event to all matching subscriptions
            await self._route_event(event)
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history for replay."""
        if self.replay_enabled:
            self.event_history.append(event)
            
            # Limit history size
            if len(self.event_history) > self.max_history_size:
                self.event_history = self.event_history[-self.max_history_size:]
    
    async def _cleanup_loop(self) -> None:
        """Cleanup loop for expired subscriptions and connections."""
        self.logger.info("Cleanup loop started")
        
        try:
            while self.running:
                await asyncio.sleep(60)  # Run every minute
                
                # Check agent health
                await self.agent_registry.check_health()
                
                # Clean up inactive subscriptions
                current_time = datetime.now()
                expired_subscriptions = []
                
                for sub_id, subscription in self.subscriptions.items():
                    # Remove subscriptions for disconnected clients
                    if (
                        subscription.endpoint
                        and subscription.endpoint not in self.active_connections
                    ):
                        expired_subscriptions.append(sub_id)
                    
                    # Reset circuit breakers after cooldown period
                    if subscription.circuit_breaker_open:
                        if subscription.last_delivery:
                            cooldown = timedelta(minutes=5)
                            if current_time - subscription.last_delivery > cooldown:
                                subscription.reset_circuit_breaker()
                                self.logger.info(
                                    f"Reset circuit breaker for subscription {sub_id}"
                                )
                
                for sub_id in expired_subscriptions:
                    del self.subscriptions[sub_id]
                    self.logger.info(f"Cleaned up expired subscription: {sub_id}")
                
                # Clean up stale connections
                stale_connections = []
                for client_id, connection in self.active_connections.items():
                    last_activity = connection["last_activity"]
                    if current_time - last_activity > timedelta(minutes=30):
                        stale_connections.append(client_id)
                
                for client_id in stale_connections:
                    connection = self.active_connections.pop(client_id)
                    try:
                        writer = connection["writer"]
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        pass
                    self.logger.info(f"Cleaned up stale connection: {client_id}")
                
                # Update statistics
                self.stats.active_subscriptions = len([
                    s for s in self.subscriptions.values() if s.active
                ])
                self.stats.circuit_breakers_open = len([
                    s for s in self.subscriptions.values() if s.circuit_breaker_open
                ])
                self.stats.dead_letter_count = len(self.dead_letter_queue.entries)
        
        except asyncio.CancelledError:
            self.logger.info("Cleanup loop cancelled")
    
    # Public API methods
    
    async def publish_event(self, event: Event) -> None:
        """Publish an event to the router."""
        await self.event_queue.put(event)
        self.logger.debug(f"Event {event.id} queued for processing")
    
    async def publish_batch(self, events: List[Event]) -> List[str]:
        """Publish multiple events to the router."""
        await self.event_queue.put_batch(events)
        event_ids = [event.id for event in events]
        self.logger.debug(f"Batch of {len(events)} events queued for processing")
        return event_ids
    
    def subscribe(
        self,
        subscriber_id: str,
        event_filter: Optional[EventFilter] = None,
        callback: Optional[Callable[[Event], None]] = None,
        group_id: Optional[str] = None,
    ) -> str:
        """Subscribe to events with optional filtering."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            subscriber_id=subscriber_id,
            subscription_type=SubscriptionType.FILTERED if event_filter else SubscriptionType.ALL,
            filter=event_filter,
            callback=callback,
            endpoint=None,
        )
        
        self.subscriptions[subscription.id] = subscription
        
        # Add to subscriber group for load balancing
        if group_id:
            self.subscriber_groups[group_id].append(subscription.id)
        
        self.logger.info(f"Created subscription {subscription.id} for {subscriber_id}")
        
        return subscription.id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            
            # Remove from subscriber groups
            for group_id, members in self.subscriber_groups.items():
                if subscription_id in members:
                    members.remove(subscription_id)
            
            self.logger.info(f"Removed subscription {subscription_id}")
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event processing statistics."""
        stats_dict = self.stats.to_dict()
        stats_dict.update(self.dead_letter_queue.get_statistics())
        return stats_dict
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history."""
        recent_events = self.event_history[-limit:] if limit > 0 else self.event_history
        return [event.to_dict() for event in recent_events]
    
    def health_check(self) -> Dict[str, Any]:
        """Get service health information."""
        return {
            "status": "running" if self.running else "stopped",
            "active_connections": len(self.active_connections),
            "active_subscriptions": len([
                s for s in self.subscriptions.values() if s.active
            ]),
            "queue_size": self.event_queue.qsize(),
            "total_events_processed": self.stats.total_events,
            "average_processing_time": self.stats.average_processing_time,
            "failed_deliveries": self.stats.failed_deliveries,
            "successful_deliveries": self.stats.successful_deliveries,
            "dead_letter_queue_size": len(self.dead_letter_queue.entries),
            "circuit_breakers_open": self.stats.circuit_breakers_open,
            "registered_agents": len(self.agent_registry.agents),
            "uptime": datetime.now().isoformat() if self.running else None,
        }


class EventRouterClient:
    """Client for connecting to the event router service."""
    
    def __init__(self, host: str = "localhost", port: int = 9090):
        """Initialize the event router client."""
        self.host = host
        self.port = port
        self.connected = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.logger = logging.getLogger("event_router_client")
        self.message_handlers: Dict[str, Callable] = {}
        self.listener_task: Optional[asyncio.Task] = None
        self.agent_id: Optional[str] = None
    
    async def connect(self) -> bool:
        """Connect to the event router service."""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host,
                self.port,
            )
            self.connected = True
            
            # Start message listener
            self.listener_task = asyncio.create_task(self._listen_for_messages())
            
            self.logger.info(f"Connected to event router at {self.host}:{self.port}")
            return True
        
        except Exception as e:
            self.logger.exception(f"Failed to connect to event router: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the event router service."""
        if not self.connected:
            return
        
        self.connected = False
        
        if self.listener_task:
            self.listener_task.cancel()
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        
        self.logger.info("Disconnected from event router")
    
    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Register as an agent."""
        if not self.connected:
            return False
        
        try:
            self.agent_id = agent_id
            message = {
                "type": "register_agent",
                "agent": {
                    "id": agent_id,
                    "type": agent_type,
                    "capabilities": capabilities,
                    "metadata": metadata or {},
                },
            }
            
            await self._send_message(message)
            return True
        
        except Exception as e:
            self.logger.exception(f"Failed to register agent: {e}")
            return False
    
    async def heartbeat(self) -> bool:
        """Send heartbeat to maintain agent registration."""
        if not self.connected or not self.agent_id:
            return False
        
        try:
            message = {
                "type": "agent_heartbeat",
                "agent_id": self.agent_id,
            }
            
            await self._send_message(message)
            return True
        
        except Exception as e:
            self.logger.exception(f"Failed to send heartbeat: {e}")
            return False
    
    async def publish_event(self, event: Event) -> bool:
        """Publish an event."""
        if not self.connected:
            return False
        
        try:
            message = {"type": "publish_event", "event": event.to_dict()}
            await self._send_message(message)
            return True
        
        except Exception as e:
            self.logger.exception(f"Failed to publish event: {e}")
            return False
    
    async def publish_batch(self, events: List[Event]) -> bool:
        """Publish multiple events."""
        if not self.connected:
            return False
        
        try:
            message = {
                "type": "publish_batch",
                "events": [event.to_dict() for event in events],
            }
            await self._send_message(message)
            return True
        
        except Exception as e:
            self.logger.exception(f"Failed to publish batch: {e}")
            return False
    
    async def subscribe(
        self,
        event_filter: Optional[EventFilter] = None,
        subscription_type: SubscriptionType = SubscriptionType.FILTERED,
        group_id: Optional[str] = None,
    ) -> Optional[str]:
        """Subscribe to events."""
        if not self.connected:
            return None
        
        try:
            filter_dict = {}
            if event_filter:
                if event_filter.event_types:
                    filter_dict["event_types"] = [t.value for t in event_filter.event_types]
                if event_filter.sources:
                    filter_dict["sources"] = event_filter.sources
                if event_filter.targets:
                    filter_dict["targets"] = event_filter.targets
                if event_filter.priorities:
                    filter_dict["priorities"] = [p.value for p in event_filter.priorities]
                if event_filter.pattern:
                    filter_dict["pattern"] = event_filter.pattern
            
            message = {
                "type": "subscribe",
                "subscription": {
                    "type": subscription_type.value,
                    "filter": filter_dict,
                    "group_id": group_id,
                },
            }
            
            await self._send_message(message)
            # Would need to wait for subscription_created response to get ID
            return "pending"  # Placeholder
        
        except Exception as e:
            self.logger.exception(f"Failed to subscribe: {e}")
            return None
    
    async def request_replay(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
    ) -> bool:
        """Request event replay."""
        if not self.connected:
            return False
        
        try:
            filter_dict = {}
            if start_time:
                filter_dict["start_time"] = start_time.isoformat()
            if end_time:
                filter_dict["end_time"] = end_time.isoformat()
            if event_types:
                filter_dict["event_types"] = event_types
            
            message = {
                "type": "replay_events",
                "filter": filter_dict,
            }
            
            await self._send_message(message)
            return True
        
        except Exception as e:
            self.logger.exception(f"Failed to request replay: {e}")
            return False
    
    async def _send_message(self, message: Dict[str, Any]) -> None:
        """Send message to server."""
        if not self.writer:
            raise Exception("Not connected")
        
        message_data = json.dumps(message).encode("utf-8")
        length_prefix = len(message_data).to_bytes(4, byteorder="big")
        
        self.writer.write(length_prefix + message_data)
        await self.writer.drain()
    
    async def _listen_for_messages(self) -> None:
        """Listen for messages from server."""
        try:
            while self.connected and self.reader:
                # Read message length
                length_data = await self.reader.read(4)
                if not length_data:
                    break
                
                message_length = int.from_bytes(length_data, byteorder="big")
                
                # Read message data
                message_data = await self.reader.read(message_length)
                if not message_data:
                    break
                
                # Parse and handle message
                message = json.loads(message_data.decode("utf-8"))
                await self._handle_message(message)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.exception(f"Error listening for messages: {e}")
            self.connected = False
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message from server."""
        message_type = message.get("type", "unknown")
        
        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](message)
            except Exception as e:
                self.logger.exception(f"Error handling message type {message_type}: {e}")
        else:
            self.logger.debug(f"Unhandled message type: {message_type}")
    
    def set_message_handler(self, message_type: str, handler: Callable) -> None:
        """Set handler for specific message type."""
        self.message_handlers[message_type] = handler