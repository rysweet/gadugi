#!/usr/bin/env python3
"""
Agent Interface for Hierarchical Memory System

This module provides a simple interface for agents to interact with the memory system,
including permission management and common memory access patterns.
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

from memory_manager import MemoryManager, MemoryLevel


class AgentPermissions:
    """Define memory access permissions for different agent types"""
    
    # Permission matrix: agent_type -> allowed memory levels
    PERMISSIONS = {
        # Top-level orchestration agents
        "orchestrator-agent": {
            "read": MemoryLevel.ALL_LEVELS,
            "write": [MemoryLevel.PROJECT, MemoryLevel.AGENT, MemoryLevel.TASK]
        },
        "workflow-manager": {
            "read": MemoryLevel.ALL_LEVELS,
            "write": [MemoryLevel.PROJECT, MemoryLevel.AGENT, MemoryLevel.TASK]
        },
        
        # Specialized agents
        "code-reviewer": {
            "read": [MemoryLevel.PROJECT, MemoryLevel.TEAM, MemoryLevel.AGENT, MemoryLevel.KNOWLEDGE],
            "write": [MemoryLevel.AGENT]
        },
        "task-analyzer": {
            "read": [MemoryLevel.PROJECT, MemoryLevel.TEAM, MemoryLevel.AGENT],
            "write": [MemoryLevel.AGENT, MemoryLevel.TASK]
        },
        "prompt-writer": {
            "read": MemoryLevel.ALL_LEVELS,
            "write": [MemoryLevel.AGENT, MemoryLevel.TASK]
        },
        
        # Memory management agents
        "memory-manager": {
            "read": MemoryLevel.ALL_LEVELS,
            "write": MemoryLevel.ALL_LEVELS
        },
        "project-memory-agent": {
            "read": MemoryLevel.ALL_LEVELS,
            "write": [MemoryLevel.PROJECT]
        },
        "team-memory-agent": {
            "read": MemoryLevel.ALL_LEVELS,
            "write": [MemoryLevel.TEAM]
        },
        
        # Default permissions for unknown agents
        "default": {
            "read": [MemoryLevel.PROJECT, MemoryLevel.TEAM, MemoryLevel.KNOWLEDGE],
            "write": [MemoryLevel.TASK]
        }
    }


class AgentMemoryInterface:
    """
    Simple interface for agents to interact with the hierarchical memory system.
    
    Provides permission-based access control and common memory operations.
    """
    
    def __init__(self, agent_id: str, agent_type: str, repo_path: Optional[str] = None):
        """
        Initialize agent memory interface
        
        Args:
            agent_id: Unique identifier for the agent instance
            agent_type: Type of agent (e.g., 'orchestrator-agent', 'code-reviewer')
            repo_path: Path to repository root
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.memory_manager = MemoryManager(repo_path)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Get permissions for this agent type
        self.permissions = AgentPermissions.PERMISSIONS.get(
            agent_type,
            AgentPermissions.PERMISSIONS["default"]
        )
    
    def can_read(self, level: str) -> bool:
        """Check if agent has read permission for a memory level"""
        allowed_levels = self.permissions.get("read", [])
        if allowed_levels == MemoryLevel.ALL_LEVELS:
            return level in MemoryLevel.ALL_LEVELS
        return level in allowed_levels
    
    def can_write(self, level: str) -> bool:
        """Check if agent has write permission for a memory level"""
        allowed_levels = self.permissions.get("write", [])
        if allowed_levels == MemoryLevel.ALL_LEVELS:
            return level in MemoryLevel.ALL_LEVELS
        return level in allowed_levels
    
    def read_memory(self, level: str, filename: str) -> Optional[Dict[str, Any]]:
        """
        Read a memory file with permission check
        
        Args:
            level: Memory level
            filename: Memory filename (without .md)
            
        Returns:
            Memory data or None if access denied
        """
        if not self.can_read(level):
            self.logger.warning(
                f"Agent {self.agent_id} ({self.agent_type}) denied read access to {level}/{filename}"
            )
            return None
        
        try:
            return self.memory_manager.read_memory(level, filename)
        except Exception as e:
            self.logger.error(f"Error reading memory {level}/{filename}: {e}")
            return None
    
    def add_memory_entry(self, level: str, filename: str, section: str, content: str) -> bool:
        """
        Add a memory entry with permission check
        
        Args:
            level: Memory level
            filename: Memory filename (without .md)
            section: Section name
            content: Entry content
            
        Returns:
            True if successful, False otherwise
        """
        if not self.can_write(level):
            self.logger.warning(
                f"Agent {self.agent_id} ({self.agent_type}) denied write access to {level}/{filename}"
            )
            return False
        
        try:
            self.memory_manager.add_memory_entry(level, filename, section, content)
            self.logger.info(f"Added memory entry to {level}/{filename}/{section}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding memory entry: {e}")
            return False
    
    def get_project_context(self) -> Optional[Dict[str, Any]]:
        """Get the main project context (convenience method)"""
        return self.read_memory(MemoryLevel.PROJECT, "context")
    
    def get_team_workflow(self) -> Optional[Dict[str, Any]]:
        """Get team workflow information (convenience method)"""
        return self.read_memory(MemoryLevel.TEAM, "workflow")
    
    def get_agent_memory(self) -> Optional[Dict[str, Any]]:
        """Get this agent's specific memory file"""
        agent_filename = self.agent_type.replace('-', '_')
        return self.read_memory(MemoryLevel.AGENT, agent_filename)
    
    def record_agent_memory(self, section: str, content: str) -> bool:
        """Record a memory entry in this agent's memory file"""
        agent_filename = self.agent_type.replace('-', '_')
        return self.add_memory_entry(MemoryLevel.AGENT, agent_filename, section, content)
    
    def create_task_memory(self, task_id: str, initial_content: Dict[str, List[str]]) -> bool:
        """
        Create a new task-specific memory file
        
        Args:
            task_id: Unique task identifier
            initial_content: Initial sections and content
            
        Returns:
            True if successful
        """
        if not self.can_write(MemoryLevel.TASK):
            self.logger.warning(f"Agent {self.agent_id} cannot create task memories")
            return False
        
        try:
            self.memory_manager.write_memory(
                MemoryLevel.TASK,
                task_id,
                f"Task Memory: {task_id}",
                initial_content,
                metadata={
                    "managed_by": self.agent_id,
                    "security_level": "private"
                }
            )
            return True
        except Exception as e:
            self.logger.error(f"Error creating task memory: {e}")
            return False
    
    def search_accessible_memories(self, query: str) -> List[Tuple[str, str, str]]:
        """
        Search memories that this agent can access
        
        Args:
            query: Search query
            
        Returns:
            List of (level, filename, match) tuples
        """
        all_results = self.memory_manager.search_memories(query)
        
        # Filter by read permissions
        filtered_results = []
        for level, filename, match in all_results:
            if self.can_read(level):
                filtered_results.append((level, filename, match))
        
        return filtered_results
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of accessible memories"""
        summary = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "permissions": self.permissions,
            "accessible_memories": {}
        }
        
        all_memories = self.memory_manager.list_memories()
        
        for level, files in all_memories.items():
            if self.can_read(level):
                summary["accessible_memories"][level] = {
                    "files": files,
                    "can_write": self.can_write(level)
                }
        
        return summary


# Example usage functions for agents
def get_memory_interface(agent_id: str, agent_type: str) -> AgentMemoryInterface:
    """
    Factory function to create memory interface for an agent
    
    Args:
        agent_id: Unique agent identifier
        agent_type: Type of agent
        
    Returns:
        Configured AgentMemoryInterface instance
    """
    return AgentMemoryInterface(agent_id, agent_type)


# Simple example demonstrating agent memory access
if __name__ == "__main__":
    # Example: OrchestratorAgent accessing memories
    orchestrator = AgentMemoryInterface("orch-001", "orchestrator-agent")
    
    # Read project context
    project_context = orchestrator.get_project_context()
    if project_context and project_context["exists"]:
        print("Project Context:", project_context["metadata"])
    
    # Record an agent-specific memory
    orchestrator.record_agent_memory(
        "Task Completions",
        "Successfully orchestrated parallel execution of 3 tasks"
    )
    
    # Get memory summary
    summary = orchestrator.get_memory_summary()
    print("\nMemory Summary:", summary)