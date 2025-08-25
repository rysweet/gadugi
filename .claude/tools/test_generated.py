from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from typing import Any, Dict, List, Optional

@dataclass
class Task:
    """Task with full type safety."""

    # Required fields
    id: str
    name: str

    # Optional fields
    priority: int = 1
    description: Optional[str] = None

    # Collection fields
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate after initialization."""
        if not self.name: raise ValueError('Name cannot be empty')

    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority >= 5

    def add_tag(self, tag: str) -> None:
        """Add a tag to the task."""
        if tag not in self.tags:
            self.tags.append(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "description": self.description,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


# Test the generated code
if __name__ == "__main__":
    # Create instance - all type-safe
    task = Task(
        id="task-1",
        name="Test Task",
        priority=5,
        description="This is a test",
        tags=["test", "example"],
        metadata={"key": "value"}
    )
    
    # Test methods
    assert task.is_high_priority()
    task.add_tag("new-tag")
    
    # Convert to dict
    result = task.to_dict()
    print(f"Task dict: {result}")
    
    # Type checking will validate all of this
    print("✅ All type checks should pass!")