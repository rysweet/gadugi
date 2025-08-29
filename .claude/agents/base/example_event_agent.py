#!/usr/bin/env python3
"""
Example usage of V03Agent with event publishing capabilities.

This demonstrates how to create a v0.3 agent that automatically emits events
for lifecycle management, task tracking, and collaboration.
"""

import asyncio
from datetime import datetime
from v03_agent import V03Agent, AgentCapabilities, EventConfiguration, TaskOutcome


class MyCustomAgent(V03Agent):
    """Example custom agent with event publishing."""

    def __init__(self, agent_id: str = None):
        # Define agent capabilities
        capabilities = AgentCapabilities(
            can_parallelize=True,
            can_write_code=True,
            can_review_code=True,
            can_test=True,
            expertise_areas=["python", "testing", "automation", "event_systems"],
            max_parallel_tasks=3
        )

        # Configure event publishing
        event_config = EventConfiguration(
            enabled=True,
            event_router_url="http://localhost:8000",
            timeout_seconds=5,
            retry_attempts=3,
            batch_size=20,
            emit_heartbeat=True,
            heartbeat_interval=30,  # Every 30 seconds
            store_in_memory=True,   # Store important events in agent memory
            graceful_degradation=True  # Continue working if event router is down
        )

        super().__init__(
            agent_id=agent_id or f"custom-agent-{datetime.now().strftime('%H%M%S')}",
            agent_type="custom-agent",
            capabilities=capabilities,
            event_config=event_config
        )

    async def execute_task(self, task):
        """Execute a custom task with automatic event publishing."""
        task_description = task.get('description', 'Unknown task')
        task_type = task.get('type', 'generic')

        print(f"🔧 Executing {task_type}: {task_description}")

        start_time = datetime.now()
        steps_taken = []

        try:
            # Simulate task execution with steps
            steps = [
                "Analyzing requirements",
                "Planning approach",
                "Implementing solution",
                "Testing solution",
                "Validating results"
            ]

            for i, step in enumerate(steps, 1):
                print(f"   Step {i}/5: {step}")
                steps_taken.append(step)

                # Simulate work
                await asyncio.sleep(0.2)

                # Learn something new (triggers knowledge event)
                if i == 3:  # During implementation
                    await self.emit_knowledge_learned(
                        knowledge_type="implementation_pattern",
                        content=f"Learned new pattern while {step.lower()}",
                        confidence=0.8,
                        source=task_description
                    )

            # Collaborate with other agents
            await self.emit_collaboration(
                message=f"Completed {task_type} successfully. Results available for review.",
                message_type="completion_notification",
                decision="Task completed successfully"
            )

            duration = (datetime.now() - start_time).total_seconds()

            # Return successful outcome (triggers task completion event)
            return TaskOutcome(
                success=True,
                task_id=self.current_task_id or f"task_{hash(task_description) % 1000:03d}",
                task_type=task_type,
                steps_taken=steps_taken,
                duration_seconds=duration,
                lessons_learned=f"Successfully completed {task_type} using standard approach"
            )

        except Exception as e:
            # Emit error event
            await self.emit_error(
                error_type="task_execution_error",
                error_message=str(e),
                context={"task": task, "steps_completed": len(steps_taken)}
            )

            duration = (datetime.now() - start_time).total_seconds()

            return TaskOutcome(
                success=False,
                task_id=self.current_task_id or f"task_{hash(task_description) % 1000:03d}",
                task_type=task_type,
                steps_taken=steps_taken,
                duration_seconds=duration,
                error=str(e),
                lessons_learned=f"Failed during {task_type}: {e}"
            )


async def demonstrate_event_agent():
    """Demonstrate the event-enabled agent."""
    print("="*60)
    print("V03Agent Event Publishing Demonstration")
    print("="*60)

    # Create agent
    agent = MyCustomAgent("demo-agent-001")

    try:
        # Initialize (emits initialization event)
        print("\n1. Initializing agent...")
        await agent.initialize()

        # Start and execute tasks (emits task events)
        print("\n2. Executing tasks...")

        tasks = [
            {"description": "Implement user authentication", "type": "feature_development"},
            {"description": "Write unit tests for API", "type": "test_development"},
            {"description": "Review code for security issues", "type": "code_review"}
        ]

        for i, task in enumerate(tasks, 1):
            print(f"\n   Task {i}/3:")
            task_id = await agent.start_task(task["description"])
            outcome = await agent.execute_task(task)
            await agent.learn_from_outcome(outcome)

        # Demonstrate collaboration
        print("\n3. Collaborating with other agents...")
        await agent.emit_collaboration(
            message="All assigned tasks completed. Ready for next assignment.",
            message_type="status_update",
            requires_response=False
        )

        # Show statistics
        print(f"\n4. Agent Statistics:")
        print(f"   - Tasks completed: {agent.tasks_completed}")
        print(f"   - Success rate: {agent.success_rate:.1%}")
        print(f"   - Event publishing: {'✅ Enabled' if agent._event_publishing_enabled else '❌ Disabled'}")
        print(f"   - Batched events: {len(agent._event_batch)}")

        # Flush any remaining events
        if agent._event_batch:
            print(f"\n5. Flushing batched events...")
            flushed = await agent.flush_event_batch()
            print(f"   - Attempted to send {len(agent._event_batch)} events")
            print(f"   - Successfully sent: {flushed}")

        print(f"\n✅ Demonstration completed successfully!")

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Shutdown (emits shutdown event)
        print(f"\n6. Shutting down agent...")
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(demonstrate_event_agent())
