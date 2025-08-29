"""Neo4j client for persistent memory storage."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncSession, AsyncDriver, Record, Query
from neo4j.exceptions import ServiceUnavailable

from .models import Context, ContextState, Memory, MemoryType


class Neo4jMemoryClient:
    """Neo4j client for memory persistence and graph operations."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "neo4j",
    ):
        """Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
            database: Database name
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database

        self.logger = logging.getLogger(__name__)
        self._driver: Optional[AsyncDriver] = None

    async def connect(self) -> None:
        """Connect to Neo4j database."""
        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
            # Test connection
            async with self._driver.session(database=self.database) as session:
                await session.run("RETURN 1")

            # Create indexes for performance
            await self._create_indexes()

            self.logger.info(f"Connected to Neo4j at {self.uri}")
        except ServiceUnavailable as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Neo4j database."""
        if self._driver:
            await self._driver.close()
            self.logger.info("Disconnected from Neo4j")

    async def _create_indexes(self) -> None:
        """Create database indexes for performance."""
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            # Memory indexes
            await session.run(
                "CREATE INDEX memory_id IF NOT EXISTS FOR (m:Memory) ON (m.id)"
            )
            await session.run(
                "CREATE INDEX memory_agent IF NOT EXISTS FOR (m:Memory) ON (m.agent_id)"
            )
            await session.run(
                "CREATE INDEX memory_type IF NOT EXISTS FOR (m:Memory) ON (m.type)"
            )
            await session.run(
                "CREATE INDEX memory_importance IF NOT EXISTS FOR (m:Memory) ON (m.importance_score)"
            )

            # Context indexes
            await session.run(
                "CREATE INDEX context_id IF NOT EXISTS FOR (c:Context) ON (c.id)"
            )
            await session.run(
                "CREATE INDEX context_agent IF NOT EXISTS FOR (c:Context) ON (c.agent_id)"
            )

            # Full-text search index
            await session.run("""
                CREATE FULLTEXT INDEX memory_content IF NOT EXISTS
                FOR (m:Memory) ON EACH [m.content]
            """)

    # Memory Operations

    async def store_memory(self, memory: Memory) -> str:
        """Store a memory in Neo4j.

        Args:
            memory: Memory to store

        Returns:
            Memory ID
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            query = """
                MERGE (m:Memory {id: $id})
                SET m += $properties
                RETURN m.id as id
            """

            properties = {
                "id": memory.id,
                "type": memory.type.value,
                "agent_id": memory.agent_id,
                "content": memory.content,
                "tags": memory.tags,
                "metadata": json.dumps(memory.metadata),
                "importance_score": memory.importance_score,
                "access_count": memory.access_count,
                "created_at": memory.created_at.isoformat(),
                "updated_at": memory.updated_at.isoformat(),
                "last_accessed": memory.last_accessed.isoformat() if memory.last_accessed else None,
                "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
                "version": memory.version,
                "parent_id": memory.parent_id,
            }

            result = await session.run(query, id=memory.id, properties=properties)
            record = await result.single()

            # Create associations
            if memory.associations:
                await self._create_associations(session, memory.id, memory.associations)

            # Create version relationship if this is an update
            if memory.parent_id:
                await self._create_version_relationship(session, memory.id, memory.parent_id)

            if record is not None:
                return record["id"]
            raise RuntimeError("Failed to create memory")

    async def retrieve_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory from Neo4j.

        Args:
            memory_id: ID of memory to retrieve

        Returns:
            Memory object or None if not found
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            query = """
                MATCH (m:Memory {id: $id})
                OPTIONAL MATCH (m)-[:ASSOCIATED_WITH]->(a:Memory)
                RETURN m, collect(a.id) as associations
            """

            result = await session.run(query, id=memory_id)
            record = await result.single()

            if not record:
                return None

            return self._record_to_memory(dict(record)) if record else None

    async def update_memory(self, memory: Memory) -> bool:
        """Update an existing memory.

        Args:
            memory: Memory with updates

        Returns:
            True if updated, False if not found
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            # Create new version
            memory.version += 1
            memory.updated_at = datetime.now()

            # Store as new node with parent relationship
            old_id = memory.id
            memory.id = f"{old_id}_v{memory.version}"
            memory.parent_id = old_id

            await self.store_memory(memory)

            # Update original node to point to latest version
            query = """
                MATCH (m:Memory {id: $id})
                SET m.latest_version = $latest_version
                RETURN m.id
            """

            result = await session.run(
                query,
                id=old_id,
                latest_version=memory.id
            )
            record = await result.single()

            return record is not None

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from Neo4j.

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if deleted, False if not found
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            query = """
                MATCH (m:Memory {id: $id})
                DETACH DELETE m
                RETURN count(m) as deleted
            """

            result = await session.run(query, id=memory_id)
            record = await result.single()

            return record["deleted"] > 0 if record else False

    async def search_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """Search memories using full-text search and filters.

        Args:
            query: Search query
            agent_id: Filter by agent ID
            memory_types: Filter by memory types
            tags: Filter by tags
            limit: Maximum results

        Returns:
            List of matching memories
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            # Build WHERE clause
            where_clauses = []
            params = {"query": query, "limit": limit}

            if agent_id:
                where_clauses.append("m.agent_id = $agent_id")
                params["agent_id"] = agent_id

            if memory_types:
                types = [t.value for t in memory_types]
                where_clauses.append("m.type IN $types")
                params["types"] = types

            if tags:
                where_clauses.append("any(tag IN $tags WHERE tag IN m.tags)")
                params["tags"] = tags

            where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"

            # Use full-text search
            query = f"""
                CALL db.index.fulltext.queryNodes('memory_content', $query)
                YIELD node as m, score
                WHERE {where_clause}
                OPTIONAL MATCH (m)-[:ASSOCIATED_WITH]->(a:Memory)
                RETURN m, collect(a.id) as associations, score
                ORDER BY score DESC, m.importance_score DESC
                LIMIT $limit
            """

            result = await session.run(query, **params)
            memories = []

            async for record in result:
                memory = self._record_to_memory(dict(record))
                if memory:
                    memories.append(memory)

            return memories

    async def find_similar_memories(
        self,
        memory_id: str,
        threshold: float = 0.7,
        limit: int = 10,
    ) -> List[Memory]:
        """Find memories similar to a given memory.

        Args:
            memory_id: Reference memory ID
            threshold: Similarity threshold
            limit: Maximum results

        Returns:
            List of similar memories
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            # Find memories connected through associations or shared tags
            query = """
                MATCH (ref:Memory {id: $id})
                MATCH (m:Memory)
                WHERE m.id <> ref.id
                AND (
                    EXISTS((ref)-[:ASSOCIATED_WITH]-(m))
                    OR size([tag IN ref.tags WHERE tag IN m.tags]) > 0
                    OR m.agent_id = ref.agent_id
                )
                WITH m, ref,
                     size([tag IN ref.tags WHERE tag IN m.tags]) * 1.0 / size(ref.tags + m.tags) as tag_similarity,
                     CASE WHEN m.type = ref.type THEN 0.2 ELSE 0 END as type_bonus,
                     CASE WHEN EXISTS((ref)-[:ASSOCIATED_WITH]-(m)) THEN 0.3 ELSE 0 END as association_bonus
                WITH m, (tag_similarity + type_bonus + association_bonus) as similarity
                WHERE similarity >= $threshold
                OPTIONAL MATCH (m)-[:ASSOCIATED_WITH]->(a:Memory)
                RETURN m, collect(a.id) as associations, similarity
                ORDER BY similarity DESC
                LIMIT $limit
            """

            result = await session.run(
                query,
                id=memory_id,
                threshold=threshold,
                limit=limit
            )

            memories = []
            async for record in result:
                memory = self._record_to_memory(dict(record))
                if memory:
                    memories.append(memory)

            return memories

    # Context Operations

    async def save_context(self, context: Context) -> str:
        """Save agent context to Neo4j.

        Args:
            context: Context to save

        Returns:
            Context ID
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            query = """
                MERGE (c:Context {id: $id})
                SET c += $properties
                RETURN c.id as id
            """

            properties = {
                "id": context.id,
                "agent_id": context.agent_id,
                "state": context.state.value,
                "task_id": context.task_id,
                "working_memory": json.dumps(context.working_memory),
                "parent_context_id": context.parent_context_id,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
                "metadata": json.dumps(context.metadata),
            }

            result = await session.run(query, id=context.id, properties=properties)
            record = await result.single()

            # Create relationships to memories
            if context.memories:
                await self._link_context_memories(session, context.id, context.memories)

            # Create parent-child relationships
            if context.parent_context_id:
                await self._create_context_hierarchy(
                    session,
                    context.id,
                    context.parent_context_id
                )

            if record is not None:
                return record["id"]
            raise RuntimeError("Failed to save context")

    async def load_context(self, agent_id: str) -> Optional[Context]:
        """Load the active context for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Active context or None
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            query = """
                MATCH (c:Context {agent_id: $agent_id, state: 'active'})
                OPTIONAL MATCH (c)-[:CONTAINS]->(m:Memory)
                OPTIONAL MATCH (c)-[:CHILD_OF]->(p:Context)
                OPTIONAL MATCH (c)<-[:CHILD_OF]-(ch:Context)
                RETURN c,
                       collect(DISTINCT m.id) as memories,
                       p.id as parent_id,
                       collect(DISTINCT ch.id) as children
                ORDER BY c.updated_at DESC
                LIMIT 1
            """

            result = await session.run(query, agent_id=agent_id)
            record = await result.single()

            if not record:
                return None

            return self._record_to_context(dict(record)) if record else None

    async def switch_context(
        self,
        from_context_id: str,
        to_context_id: str,
    ) -> bool:
        """Switch between contexts.

        Args:
            from_context_id: Current context ID
            to_context_id: Target context ID

        Returns:
            True if successful
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            # Suspend current context
            await session.run(
                "MATCH (c:Context {id: $id}) SET c.state = 'suspended'",
                id=from_context_id
            )

            # Activate target context
            await session.run(
                "MATCH (c:Context {id: $id}) SET c.state = 'active'",
                id=to_context_id
            )

            return True

    async def merge_contexts(self, context_ids: List[str]) -> Optional[Context]:
        """Merge multiple contexts into a new one.

        Args:
            context_ids: List of context IDs to merge

        Returns:
            Merged context or None
        """
        if len(context_ids) < 2:
            return None

        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            # Get all contexts
            query = """
                MATCH (c:Context)
                WHERE c.id IN $ids
                OPTIONAL MATCH (c)-[:CONTAINS]->(m:Memory)
                RETURN c, collect(DISTINCT m.id) as memories
            """

            result = await session.run(query, ids=context_ids)

            # Merge into first context
            merged_context = None
            all_memories = set()
            merged_working_memory = {}

            async for record in result:
                context = self._record_to_context(dict(record))
                if not merged_context:
                    merged_context = context
                elif context is not None:
                    merged_context.merge_with(context)

                all_memories.update(record["memories"] or [])

                # Archive merged contexts
                if context is not None:
                    await session.run(
                        "MATCH (c:Context {id: $id}) SET c.state = 'merged'",
                        id=context.id
                    )

            if merged_context:
                merged_context.memories = list(all_memories)
                merged_context.state = ContextState.ACTIVE
                await self.save_context(merged_context)

            return merged_context

    # Memory Management Operations

    async def prune_memories(
        self,
        agent_id: Optional[str] = None,
        older_than_days: int = 90,
        preserve_important: bool = True,
        importance_threshold: float = 0.7,
    ) -> int:
        """Prune old memories based on criteria.

        Args:
            agent_id: Filter by agent ID
            older_than_days: Age threshold in days
            preserve_important: Whether to preserve important memories
            importance_threshold: Importance threshold for preservation

        Returns:
            Number of memories pruned
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            cutoff_date = (datetime.now() - timedelta(days=older_than_days)).isoformat()

            where_clauses = [f"m.updated_at < '{cutoff_date}'"]
            params = {}

            if agent_id:
                where_clauses.append("m.agent_id = $agent_id")
                params["agent_id"] = agent_id

            if preserve_important:
                where_clauses.append(f"m.importance_score < {importance_threshold}")

            where_clause = " AND ".join(where_clauses)

            # Build the query as a literal string to avoid typing issues
            base_query = """
                MATCH (m:Memory)
                WHERE {where_clause}
                WITH m
                DETACH DELETE m
                RETURN count(m) as pruned
            """.format(where_clause=where_clause)

            result = await session.run(base_query, **params)  # type: ignore[arg-type]
            record = await result.single()

            pruned_count = record["pruned"] if record else 0
            self.logger.info(f"Pruned {pruned_count} memories")

            return pruned_count

    async def consolidate_memories(
        self,
        agent_id: str,
        time_window_hours: int = 24,
    ) -> int:
        """Consolidate similar memories within a time window.

        Args:
            agent_id: Agent ID
            time_window_hours: Time window for consolidation

        Returns:
            Number of memories consolidated
        """
        if self._driver is None:
            raise RuntimeError("Driver not connected")
        async with self._driver.session(database=self.database) as session:
            # Find similar memories within time window
            query = """
                MATCH (m1:Memory {agent_id: $agent_id})
                MATCH (m2:Memory {agent_id: $agent_id})
                WHERE m1.id < m2.id
                AND abs(datetime(m1.created_at) - datetime(m2.created_at)) < duration({hours: $hours})
                AND m1.type = m2.type
                AND size([tag IN m1.tags WHERE tag IN m2.tags]) > size(m1.tags) * 0.5
                RETURN m1, m2
            """

            result = await session.run(
                query,
                agent_id=agent_id,
                hours=time_window_hours
            )

            consolidated = 0
            async for record in result:
                m1 = self._record_to_memory({"m": record["m1"], "associations": []})
                m2 = self._record_to_memory({"m": record["m2"], "associations": []})

                if m1 is not None and m2 is not None:
                    # Merge m2 into m1
                    m1.content = f"{m1.content}\n\n[Consolidated]: {m2.content}"
                    m1.importance_score = max(m1.importance_score, m2.importance_score)
                    m1.access_count += m2.access_count
                    m1.tags = list(set(m1.tags + m2.tags))

                    await self.update_memory(m1)
                    await self.delete_memory(m2.id)

                consolidated += 1

            return consolidated

    # Helper Methods

    async def _create_associations(
        self,
        session: AsyncSession,
        memory_id: str,
        association_ids: List[str],
    ) -> None:
        """Create association relationships between memories."""
        query = """
            MATCH (m:Memory {id: $id})
            MATCH (a:Memory)
            WHERE a.id IN $associations
            MERGE (m)-[:ASSOCIATED_WITH]->(a)
        """
        await session.run(query, id=memory_id, associations=association_ids)

    async def _create_version_relationship(
        self,
        session: AsyncSession,
        new_id: str,
        parent_id: str,
    ) -> None:
        """Create version relationship between memories."""
        query = """
            MATCH (new:Memory {id: $new_id})
            MATCH (parent:Memory {id: $parent_id})
            MERGE (new)-[:VERSION_OF]->(parent)
        """
        await session.run(query, new_id=new_id, parent_id=parent_id)

    async def _link_context_memories(
        self,
        session: AsyncSession,
        context_id: str,
        memory_ids: List[str],
    ) -> None:
        """Link context to memories."""
        query = """
            MATCH (c:Context {id: $context_id})
            MATCH (m:Memory)
            WHERE m.id IN $memory_ids
            MERGE (c)-[:CONTAINS]->(m)
        """
        await session.run(query, context_id=context_id, memory_ids=memory_ids)

    async def _create_context_hierarchy(
        self,
        session: AsyncSession,
        child_id: str,
        parent_id: str,
    ) -> None:
        """Create parent-child relationship between contexts."""
        query = """
            MATCH (child:Context {id: $child_id})
            MATCH (parent:Context {id: $parent_id})
            MERGE (child)-[:CHILD_OF]->(parent)
        """
        await session.run(query, child_id=child_id, parent_id=parent_id)

    def _record_to_memory(self, record: Dict[str, Any]) -> Optional[Memory]:
        """Convert Neo4j record to Memory object."""
        if not record or "m" not in record:
            return None

        node = record["m"]

        return Memory(
            id=node["id"],
            type=MemoryType(node.get("type", "semantic")),
            agent_id=node.get("agent_id", ""),
            content=node.get("content", ""),
            embedding=None,  # Would need to deserialize if stored
            tags=node.get("tags", []),
            metadata=json.loads(node.get("metadata", "{}")),
            importance_score=node.get("importance_score", 0.5),
            access_count=node.get("access_count", 0),
            created_at=datetime.fromisoformat(node.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(node.get("updated_at", datetime.now().isoformat())),
            last_accessed=datetime.fromisoformat(node["last_accessed"]) if node.get("last_accessed") else None,
            expires_at=datetime.fromisoformat(node["expires_at"]) if node.get("expires_at") else None,
            version=node.get("version", 1),
            parent_id=node.get("parent_id"),
            associations=record.get("associations", []),
        )

    def _record_to_context(self, record: Dict[str, Any]) -> Optional[Context]:
        """Convert Neo4j record to Context object."""
        if not record or "c" not in record:
            return None

        node = record["c"]

        return Context(
            id=node["id"],
            agent_id=node.get("agent_id", ""),
            state=ContextState(node.get("state", "active")),
            task_id=node.get("task_id"),
            memories=record.get("memories", []),
            working_memory=json.loads(node.get("working_memory", "{}")),
            parent_context_id=record.get("parent_id"),
            child_contexts=record.get("children", []),
            created_at=datetime.fromisoformat(node.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(node.get("updated_at", datetime.now().isoformat())),
            metadata=json.loads(node.get("metadata", "{}")),
        )
