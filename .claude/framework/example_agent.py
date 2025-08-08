"""Example agent implementation using the BaseAgent framework."""

import logging
from pathlib import Path
from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class ExampleAgent(BaseAgent):
    """Example agent that demonstrates the agent framework capabilities."""
    
    async def init(self) -> None:
        """Initialize the example agent."""
        logger.info(f"Initializing {self.metadata.name}")
        
        # Set initial state
        self.state["task_count"] = 0
        self.state["last_task"] = None
        
        # Load any saved state
        await self.load_state()
    
    async def process(self, event: Any) -> AgentResponse:
        """Process incoming events.
        
        Args:
            event: Event to process
            
        Returns:
            Processing response
        """
        try:
            event_type = event.type if hasattr(event, "type") else str(event)
            event_data = event.data if hasattr(event, "data") else {}
            
            logger.info(f"Processing event: {event_type}")
            
            # Handle different event types
            if event_type == "task.assigned":
                return await self._handle_task_assignment(event_data)
            
            elif event_type == "code.changed":
                return await self._handle_code_change(event_data)
            
            elif event_type == "agent.hasQuestion.response":
                return await self._handle_question_response(event_data)
            
            elif event_type == "agent.needsApproval.response":
                return await self._handle_approval_response(event_data)
            
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return AgentResponse(
                    success=False,
                    error=f"Unknown event type: {event_type}",
                )
        
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
            )
    
    async def _handle_task_assignment(self, data: Dict[str, Any]) -> AgentResponse:
        """Handle task assignment event."""
        task_id = data.get("task_id", "unknown")
        task_description = data.get("description", "")
        
        # Update state
        self.state["task_count"] += 1
        self.state["last_task"] = task_id
        
        # Ask for clarification if needed
        if not task_description:
            answer = await self.ask_question(
                "What should I do for this task?",
                context={"task_id": task_id},
            )
            task_description = answer
        
        # Request approval for sensitive operations
        if "delete" in task_description.lower() or "remove" in task_description.lower():
            approved = await self.request_approval(
                f"Execute task with potential destructive operation: {task_description}",
                details={"task_id": task_id},
            )
            
            if not approved:
                return AgentResponse(
                    success=False,
                    error="Task not approved by user",
                )
        
        # Use tools to complete the task
        try:
            # Example: Read a file
            if "read" in task_description.lower():
                filepath = data.get("filepath", "README.md")
                content = await self.invoke_tool(
                    "file_reader",
                    {"filepath": filepath},
                )
                
                return AgentResponse(
                    success=True,
                    result={"content": content},
                    metadata={"task_id": task_id},
                )
            
            # Example: Execute command
            elif "run" in task_description.lower() or "execute" in task_description.lower():
                command = data.get("command", "echo 'Hello World'")
                result = await self.invoke_tool(
                    "shell_command",
                    {"command": command},
                )
                
                return AgentResponse(
                    success=True,
                    result=result,
                    metadata={"task_id": task_id},
                )
            
            else:
                # Default response
                return AgentResponse(
                    success=True,
                    result=f"Task {task_id} processed",
                    metadata={"task_id": task_id, "description": task_description},
                )
        
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Failed to complete task: {e}",
            )
    
    async def _handle_code_change(self, data: Dict[str, Any]) -> AgentResponse:
        """Handle code change event."""
        filepath = data.get("filepath", "")
        change_type = data.get("change_type", "modified")
        
        logger.info(f"Code change detected: {filepath} ({change_type})")
        
        # Analyze the changed file
        if filepath:
            try:
                content = await self.invoke_tool(
                    "file_reader",
                    {"filepath": filepath},
                )
                
                # Simple analysis
                lines = content.split("\n")
                stats = {
                    "lines": len(lines),
                    "imports": sum(1 for line in lines if line.strip().startswith("import")),
                    "functions": sum(1 for line in lines if line.strip().startswith("def ")),
                    "classes": sum(1 for line in lines if line.strip().startswith("class ")),
                }
                
                return AgentResponse(
                    success=True,
                    result=stats,
                    metadata={"filepath": filepath, "change_type": change_type},
                )
            
            except Exception as e:
                return AgentResponse(
                    success=False,
                    error=f"Failed to analyze file: {e}",
                )
        
        return AgentResponse(
            success=True,
            result="Code change acknowledged",
        )
    
    async def _handle_question_response(self, data: Dict[str, Any]) -> AgentResponse:
        """Handle question response event."""
        question_id = data.get("question_id", "")
        answer = data.get("answer", "")
        
        # Provide answer to pending question
        self.answer_question(question_id, answer)
        
        return AgentResponse(
            success=True,
            result="Answer received",
        )
    
    async def _handle_approval_response(self, data: Dict[str, Any]) -> AgentResponse:
        """Handle approval response event."""
        approval_id = data.get("approval_id", "")
        approved = data.get("approved", False)
        
        # Provide approval decision
        self.provide_approval(approval_id, approved)
        
        return AgentResponse(
            success=True,
            result=f"Approval {'granted' if approved else 'denied'}",
        )
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        # Save final state
        await self.save_state()
        
        logger.info(f"Final statistics: {self.state}")
        
        # Call parent cleanup
        await super().cleanup()