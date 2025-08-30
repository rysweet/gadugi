"""Memory System Integration Service.

Integrates MCP, Neo4j, Event Router, and GitHub for unified memory management.
"""

import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .models import (
    ImportResult,
    Memory,
    MemoryType,
    Pattern,
    PruneResult,
    SyncResult,
)

# Import service dependencies
try:
    from ..mcp import MCPService  # type: ignore
    from ..event_router import EventRouter, Event, EventType, EventPriority  # type: ignore[import]
except ImportError:
    # Mock imports for development
    class MCPService:
        async def store(self, key: str, value: Any) -> None:
            pass

        async def retrieve(self, key: str) -> Any:
            return None

    class EventRouter:
        async def publish(self, event: Any) -> None:
            pass

    class Event:
        def __init__(self, **kwargs):
            pass

    class EventType:
        MEMORY_CREATED = "memory.created"
        MEMORY_UPDATED = "memory.updated"
        MEMORY_PRUNED = "memory.pruned"

    class EventPriority:
        NORMAL = "normal"


# Neo4j integration
try:
    from neo4j import AsyncGraphDatabase
except ImportError:
    AsyncGraphDatabase = None

# GitHub integration
try:
    import httpx
except ImportError:
    httpx = None


logger = logging.getLogger(__name__)


class MemorySystem:
    """Unified memory management system for Gadugi platform."""

    def __init__(
        self,
        mcp_service: Optional[MCPService] = None,
        event_router: Optional[EventRouter] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_auth: Optional[tuple[str, str]] = None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
    ):
        """Initialize the memory system.

        Args:
            mcp_service: MCP service instance for persistence
            event_router: Event router for notifications
            neo4j_uri: Neo4j database URI
            neo4j_auth: Neo4j authentication (username, password)
            github_token: GitHub API token
            github_repo: GitHub repository (owner/repo)
        """
        self.mcp_service = mcp_service or MCPService()
        self.event_router = event_router or EventRouter()

        # Neo4j setup
        self.neo4j_driver = None
        if neo4j_uri and neo4j_auth and AsyncGraphDatabase:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                neo4j_uri,
                auth=neo4j_auth,
            )

        # GitHub setup
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_repo = github_repo or os.getenv("GITHUB_REPOSITORY")
        self.github_headers = (
            {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            if self.github_token
            else {}
        )

        # Memory cache for performance
        self._memory_cache: Dict[str, Memory] = {}
        self._cache_lock = asyncio.Lock()

        # Pattern extraction state
        self._pattern_cache: List[Pattern] = []
        self._pattern_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the memory system."""
        logger.info("Initializing memory system")

        # Create Neo4j indexes if available
        if self.neo4j_driver:
            async with self.neo4j_driver.session() as session:
                await session.run("CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.id)")
                await session.run(
                    "CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.type)"
                )
                await session.run(
                    "CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.created_at)"
                )

        logger.info("Memory system initialized")

    async def store_memory(self, memory: Memory) -> str:
        """Store a memory in the system.

        Args:
            memory: Memory to store

        Returns:
            Memory ID
        """
        # Generate ID if not provided
        if not memory.id:
            memory.id = f"mem_{uuid.uuid4().hex[:8]}"

        # Update timestamp
        memory.updated_at = datetime.now()

        # Store in MCP
        await self.mcp_service.store(
            f"memory:{memory.id}",
            memory.to_dict(),
        )

        # Store in Neo4j if available
        if self.neo4j_driver:
            async with self.neo4j_driver.session() as session:
                await session.run(
                    """
                    MERGE (m:Memory {id: $id})
                    SET m += $properties
                    """,
                    id=memory.id,
                    properties={
                        "type": memory.type.value,
                        "content": memory.content,
                        "created_at": memory.created_at.isoformat(),
                        "updated_at": memory.updated_at.isoformat(),
                        "importance": memory.importance,
                        "tags": memory.tags,
                    },
                )

                # Create relationships
                for ref_id in memory.references:
                    await session.run(
                        """
                        MATCH (m1:Memory {id: $id1})
                        MATCH (m2:Memory {id: $id2})
                        MERGE (m1)-[:REFERENCES]->(m2)
                        """,
                        id1=memory.id,
                        id2=ref_id,
                    )

        # Update cache
        async with self._cache_lock:
            self._memory_cache[memory.id] = memory

        # Publish event
        await self.event_router.publish(
            Event(
                type=EventType.MEMORY_CREATED,
                source="memory_system",
                data={"memory_id": memory.id, "type": memory.type.value},
                priority=EventPriority.NORMAL,
            )
        )

        logger.info(f"Stored memory {memory.id} of type {memory.type.value}")
        return memory.id

    async def retrieve_context(
        self,
        query: str,
        limit: int = 10,
        memory_types: Optional[List[MemoryType]] = None,
    ) -> List[Memory]:
        """Retrieve relevant memories based on query.

        Args:
            query: Search query
            limit: Maximum number of memories to return
            memory_types: Filter by memory types

        Returns:
            List of relevant memories
        """
        start_time = asyncio.get_event_loop().time()
        results: List[Memory] = []

        # Use Neo4j for graph-based retrieval if available
        if self.neo4j_driver:
            async with self.neo4j_driver.session() as session:
                # Full-text search with type filtering
                type_filter = ""
                if memory_types:
                    types = [t.value for t in memory_types]
                    type_filter = f"AND m.type IN {types}"

                query_result = await session.run(
                    f"""
                    MATCH (m:Memory)
                    WHERE m.content CONTAINS $query {type_filter}
                    RETURN m
                    ORDER BY m.importance DESC, m.updated_at DESC
                    LIMIT $limit
                    """,
                    query=query,  # type: ignore
                    limit=limit,
                )

                async for record in query_result:
                    node = record["m"]
                    memory = Memory(
                        id=node["id"],
                        type=MemoryType(node["type"]),
                        content=node["content"],
                        created_at=datetime.fromisoformat(node["created_at"]),
                        updated_at=datetime.fromisoformat(node["updated_at"]),
                        importance=node.get("importance", 1.0),
                        tags=node.get("tags", []),
                    )
                    results.append(memory)

        # Fallback to cache search
        if not results:
            async with self._cache_lock:
                for memory in self._memory_cache.values():
                    if memory_types and memory.type not in memory_types:
                        continue

                    # Simple text matching
                    if query.lower() in memory.content.lower():
                        results.append(memory)
                        if len(results) >= limit:
                            break

        # Ensure we meet performance target (<200ms)
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > 0.2:
            logger.warning(f"Memory retrieval took {elapsed:.3f}s (target: <200ms)")
        else:
            logger.debug(f"Memory retrieval took {elapsed:.3f}s")

        return results[:limit]

    async def sync_with_github(self) -> SyncResult:
        """Synchronize memories with GitHub issues.

        Returns:
            Synchronization result
        """
        if not self.github_token or not self.github_repo:
            return SyncResult(
                success=False,
                errors=["GitHub credentials not configured"],
            )

        if not httpx:
            return SyncResult(
                success=False,
                errors=["httpx not installed"],
            )

        result = SyncResult(success=True)

        async with httpx.AsyncClient() as client:
            # Get TODO memories
            todos = await self.retrieve_context(
                "",
                limit=100,
                memory_types=[MemoryType.TODO],
            )

            # Get existing issues
            response = await client.get(
                f"https://api.github.com/repos/{self.github_repo}/issues",
                headers=self.github_headers,
                params={"labels": "memory-sync,ai-assistant", "state": "all"},
            )

            if response.status_code != 200:
                result.success = False
                result.errors.append(f"Failed to fetch issues: {response.text}")
                return result

            existing_issues = {issue["title"]: issue for issue in response.json()}

            # Sync TODOs to issues
            for todo in todos:
                title = todo.content.split("\n")[0][:100]  # First line as title

                if title in existing_issues:
                    # Update existing issue if needed
                    issue = existing_issues[title]
                    if todo.metadata.get("completed") and issue["state"] == "open":
                        # Close completed issue
                        response = await client.patch(
                            f"https://api.github.com/repos/{self.github_repo}/issues/{issue['number']}",
                            headers=self.github_headers,
                            json={"state": "closed"},
                        )
                        if response.status_code == 200:
                            result.issues_closed += 1
                            todo.github_issue_id = issue["number"]
                            await self.store_memory(todo)
                    else:
                        result.issues_updated += 1
                else:
                    # Create new issue
                    response = await client.post(
                        f"https://api.github.com/repos/{self.github_repo}/issues",
                        headers=self.github_headers,
                        json={
                            "title": title,
                            "body": f"{todo.content}\n\n*Created by AI Memory System*",
                            "labels": ["memory-sync", "ai-assistant"],
                        },
                    )
                    if response.status_code == 201:
                        result.issues_created += 1
                        issue_data = response.json()
                        todo.github_issue_id = issue_data["number"]
                        await self.store_memory(todo)

            # Sync issues to memories
            response = await client.get(
                f"https://api.github.com/repos/{self.github_repo}/issues",
                headers=self.github_headers,
                params={"labels": "memory-sync", "state": "open"},
            )

            if response.status_code == 200:
                for issue in response.json():
                    # Check if memory exists
                    existing = await self.retrieve_context(
                        issue["title"],
                        limit=1,
                        memory_types=[MemoryType.TODO],
                    )

                    if not existing:
                        # Create memory from issue
                        memory = Memory(
                            id=f"github_{issue['number']}",
                            type=MemoryType.TODO,
                            content=f"{issue['title']}\n\n{issue['body']}",
                            github_issue_id=issue["number"],
                            metadata={"github_url": issue["html_url"]},
                        )
                        await self.store_memory(memory)
                        result.memories_created += 1

        logger.info(f"GitHub sync completed: {result.to_dict()}")
        return result

    async def import_from_memory_md(self, filepath: Path) -> ImportResult:
        """Import memories from Memory.md file.

        Args:
            filepath: Path to Memory.md file

        Returns:
            Import result
        """
        result = ImportResult(success=True, filepath=filepath)

        if not filepath.exists():
            result.success = False
            result.errors.append(f"File not found: {filepath}")
            return result

        try:
            content = filepath.read_text()

            # Parse sections
            sections = re.split(r"^## ", content, flags=re.MULTILINE)

            for section in sections[1:]:  # Skip header
                lines = section.strip().split("\n")
                if not lines:
                    continue

                section_title = lines[0].strip()
                section_content = "\n".join(lines[1:])

                if "Todo" in section_title or "TODO" in section_title:
                    # Parse TODO items
                    todos = re.findall(r"[-*]\s+(.+)", section_content)
                    for todo_text in todos:
                        memory = Memory(
                            id=f"import_todo_{uuid.uuid4().hex[:8]}",
                            type=MemoryType.TODO,
                            content=todo_text.strip(),
                            metadata={"source": "Memory.md"},
                        )
                        await self.store_memory(memory)
                        result.todos_imported += 1

                elif "Reflection" in section_title:
                    # Store reflections
                    if section_content.strip():
                        memory = Memory(
                            id=f"import_refl_{uuid.uuid4().hex[:8]}",
                            type=MemoryType.REFLECTION,
                            content=section_content.strip(),
                            metadata={"source": "Memory.md"},
                        )
                        await self.store_memory(memory)
                        result.reflections_imported += 1

                else:
                    # Store as context memory
                    if section_content.strip():
                        memory = Memory(
                            id=f"import_ctx_{uuid.uuid4().hex[:8]}",
                            type=MemoryType.CONTEXT,
                            content=f"{section_title}\n{section_content}".strip(),
                            metadata={"source": "Memory.md"},
                        )
                        await self.store_memory(memory)
                        result.memories_imported += 1

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        logger.info(f"Memory.md import completed: {result.to_dict()}")
        return result

    async def prune_old_memories(self, days: int = 30) -> PruneResult:
        """Prune old memories from the system.

        Args:
            days: Age threshold in days

        Returns:
            Prune result
        """
        result = PruneResult(success=True)
        cutoff_date = datetime.now() - timedelta(days=days)

        try:
            # Get old memories from Neo4j
            if self.neo4j_driver:
                async with self.neo4j_driver.session() as session:
                    # Find old, low-importance memories
                    query_result = await session.run(
                        """
                        MATCH (m:Memory)
                        WHERE m.updated_at < $cutoff
                        AND m.importance < 0.5
                        AND NOT (m)-[:REFERENCES]-()
                        RETURN m.id as id
                        """,
                        cutoff=cutoff_date.isoformat(),
                    )

                    memory_ids: Set[str] = set()
                    async for record in query_result:
                        memory_ids.add(record["id"])

                    # Archive memories (store to file before deletion)
                    archive_path = (
                        Path(".memory_archive")
                        / f"archive_{datetime.now():%Y%m%d}.json"
                    )
                    archive_path.parent.mkdir(exist_ok=True)

                    archived_memories = []
                    for mem_id in memory_ids:
                        memory_data = await self.mcp_service.retrieve(
                            f"memory:{mem_id}"
                        )
                        if memory_data:
                            archived_memories.append(memory_data)

                    if archived_memories:
                        with open(archive_path, "w") as f:
                            json.dump(archived_memories, f, indent=2)
                        result.memories_archived = len(archived_memories)

                    # Delete from Neo4j
                    await session.run(
                        """
                        MATCH (m:Memory)
                        WHERE m.id IN $ids
                        DETACH DELETE m
                        """,
                        ids=list(memory_ids),
                    )

                    result.memories_pruned = len(memory_ids)

            # Clear from cache
            async with self._cache_lock:
                old_cache_size = len(self._memory_cache)
                self._memory_cache = {
                    k: v
                    for k, v in self._memory_cache.items()
                    if v.updated_at >= cutoff_date
                }
                cache_cleared = old_cache_size - len(self._memory_cache)
                result.memories_pruned += cache_cleared

            # Publish event
            if result.memories_pruned > 0:
                await self.event_router.publish(
                    Event(
                        type=EventType.MEMORY_PRUNED,
                        source="memory_system",
                        data={
                            "memories_pruned": result.memories_pruned,
                            "memories_archived": result.memories_archived,
                        },
                        priority=EventPriority.NORMAL,
                    )
                )

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        logger.info(f"Memory pruning completed: {result.to_dict()}")
        return result

    async def extract_patterns(self) -> List[Pattern]:
        """Extract patterns from stored memories.

        Returns:
            List of discovered patterns
        """
        patterns: List[Pattern] = []

        if self.neo4j_driver:
            async with self.neo4j_driver.session() as session:
                # Find frequently connected memories
                query_result = await session.run(
                    """
                    MATCH (m1:Memory)-[r:REFERENCES]-(m2:Memory)
                    WITH m1.type as type1, m2.type as type2, COUNT(r) as frequency
                    WHERE frequency > 2
                    RETURN type1, type2, frequency
                    ORDER BY frequency DESC
                    LIMIT 10
                    """
                )

                async for record in query_result:
                    pattern = Pattern(
                        id=f"pattern_{uuid.uuid4().hex[:8]}",
                        pattern_type="reference_frequency",
                        description=f"{record['type1']} frequently references {record['type2']}",
                        frequency=record["frequency"],
                        memory_ids=[],
                        confidence=min(record["frequency"] / 10.0, 1.0),
                    )
                    patterns.append(pattern)

                # Find task completion patterns
                query_result = await session.run(
                    """
                    MATCH (m:Memory {type: 'todo'})
                    WHERE m.metadata.completed = true
                    WITH DATE(m.updated_at) as completion_date, COUNT(m) as tasks_completed
                    RETURN completion_date, tasks_completed
                    ORDER BY completion_date DESC
                    LIMIT 30
                    """
                )

                completion_data = []
                async for record in query_result:
                    completion_data.append(record["tasks_completed"])

                if completion_data:
                    avg_completion = sum(completion_data) / len(completion_data)
                    pattern = Pattern(
                        id=f"pattern_{uuid.uuid4().hex[:8]}",
                        pattern_type="task_completion_rate",
                        description=f"Average {avg_completion:.1f} tasks completed per day",
                        frequency=len(completion_data),
                        memory_ids=[],
                        confidence=0.8,
                        metadata={"average": avg_completion},
                    )
                    patterns.append(pattern)

        # Update pattern cache
        async with self._pattern_lock:
            self._pattern_cache = patterns

        logger.info(f"Extracted {len(patterns)} patterns from memories")
        return patterns

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.neo4j_driver:
            await self.neo4j_driver.close()

        logger.info("Memory system cleaned up")
