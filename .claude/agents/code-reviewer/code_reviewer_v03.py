"""
Code Reviewer Agent V0.3 with Memory Integration
==============================================

Production-grade code reviewer that learns from past reviews and patterns.
Tracks which issues get accepted/rejected and adapts recommendations.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

# Import V03Agent base class
from ..base.v03_agent import V03Agent, AgentCapabilities, TaskOutcome
from ...shared.memory_integration import AgentMemoryInterface
from ...engines.code_reviewer_engine import CodeReviewerEngine, ReviewResult, ReviewStatus, IssueType, IssueCategory


@dataclass
class ReviewFeedback:
    """Tracks feedback on review issues."""
    issue_id: str
    issue_type: str
    category: str
    rule_id: str
    developer: str
    module: str
    file_path: str
    accepted: bool
    feedback_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DeveloperPattern:
    """Tracks patterns for a specific developer."""
    developer: str
    common_issues: Dict[str, int] = field(default_factory=dict)
    ignored_rules: Set[str] = field(default_factory=set)
    preferred_patterns: List[str] = field(default_factory=list)
    last_reviewed: Optional[datetime] = None


@dataclass
class ModulePattern:
    """Tracks patterns for a specific module/file."""
    module_path: str
    frequent_issues: Dict[str, int] = field(default_factory=dict)
    complexity_trends: List[float] = field(default_factory=list)
    security_hotspots: List[str] = field(default_factory=list)
    last_reviewed: Optional[datetime] = None


class CodeReviewerV03(V03Agent):
    """
    V0.3 Code Reviewer with Memory and Learning Capabilities.

    Features:
    - Memory of past reviews and patterns
    - Learning from accepted/rejected feedback
    - Developer-specific pattern recognition
    - Module-specific issue tracking
    - Adaptive recommendation system
    """

    def __init__(self):
        capabilities = AgentCapabilities(
            can_review_code=True,
            can_parallelize=True,  # Can review multiple files in parallel
            can_test=True,  # Can run tests and quality tools
            expertise_areas=[
                "python", "code_quality", "security", "performance",
                "testing", "documentation", "design_patterns"
            ],
            max_parallel_tasks=5
        )

        super().__init__(
            agent_id="code_reviewer_v03",
            agent_type="code-reviewer",
            capabilities=capabilities
        )

        # Code review engine
        self.review_engine: Optional[CodeReviewerEngine] = None

        # Learning and pattern tracking
        self.developer_patterns: Dict[str, DeveloperPattern] = {}
        self.module_patterns: Dict[str, ModulePattern] = {}
        self.review_history: List[ReviewFeedback] = []

        # Configuration
        self.config = {
            "learning_enabled": True,
            "pattern_tracking_enabled": True,
            "min_feedback_for_pattern": 3,
            "pattern_confidence_threshold": 0.7,
            "adaptive_scoring": True
        }

        self.logger = logging.getLogger(__name__)

    async def initialize(self, mcp_url: str = "http://localhost:8000") -> None:
        """Initialize the agent with memory system and load patterns."""
        await super().initialize(mcp_url)

        # Initialize code review engine
        self.review_engine = CodeReviewerEngine()

        # Migrate legacy data if needed
        await self._migrate_legacy_data()

        # Load historical patterns from memory
        await self._load_historical_patterns()

        self.logger.info("Code Reviewer V0.3 initialized with learning capabilities")

    async def _load_historical_patterns(self) -> None:
        """Load historical patterns from long-term memory."""
        try:
            # Search for pattern-related memories
            if not self.memory:
                self.logger.warning("Memory not initialized, skipping pattern loading")
                return
            
            pattern_memories = await self.memory.search_memories(
                tags=["pattern", "developer", "module"],
                limit=100
            )

            # Rebuild patterns from memories
            for memory in pattern_memories:
                content = memory.get('content', '')
                if 'developer_pattern:' in content:
                    await self._parse_developer_pattern_memory(content)
                elif 'module_pattern:' in content:
                    await self._parse_module_pattern_memory(content)

            self.logger.info(f"Loaded {len(self.developer_patterns)} developer patterns and {len(self.module_patterns)} module patterns")

        except Exception as e:
            self.logger.warning(f"Could not load historical patterns: {e}")

    async def _parse_developer_pattern_memory(self, content: str) -> None:
        """Parse developer pattern from memory content."""
        try:
            # Simple parsing - in production would use more robust format
            lines = content.split('\n')
            developer = None
            for line in lines:
                if line.startswith('Developer:'):
                    developer = line.split(':', 1)[1].strip()
                    break

            if developer and developer not in self.developer_patterns:
                self.developer_patterns[developer] = DeveloperPattern(developer=developer)
        except Exception as e:
            self.logger.warning(f"Failed to parse developer pattern: {e}")

    async def _parse_module_pattern_memory(self, content: str) -> None:
        """Parse module pattern from memory content."""
        try:
            lines = content.split('\n')
            module = None
            for line in lines:
                if line.startswith('Module:'):
                    module = line.split(':', 1)[1].strip()
                    break

            if module and module not in self.module_patterns:
                self.module_patterns[module] = ModulePattern(module_path=module)
        except Exception as e:
            self.logger.warning(f"Failed to parse module pattern: {e}")

    async def _migrate_legacy_data(self) -> None:
        """Migrate legacy CodeReviewerProjectMemory.md data on first run."""
        try:
            if not self.memory:
                return
            
            # Check if migration has already been done
            existing_migration = await self.memory.search_memories(
                tags=["migration", "legacy_import"],
                limit=1
            )
            
            if existing_migration:
                self.logger.info("Legacy data migration already completed")
                return
            
            # Look for legacy file
            legacy_file = Path(".github/CodeReviewerProjectMemory.md")
            backup_file = Path(".github/CodeReviewerProjectMemory.md.bak")
            
            content = ""
            legacy_source = None
            
            # Try to read from backup first (since main file might be empty)
            if backup_file.exists():
                try:
                    content = backup_file.read_text(encoding='utf-8')
                    legacy_source = str(backup_file)
                except Exception as e:
                    self.logger.warning(f"Could not read legacy backup file: {e}")
            
            # Fall back to main file if backup not available
            if not content and legacy_file.exists():
                try:
                    content = legacy_file.read_text(encoding='utf-8')
                    legacy_source = str(legacy_file)
                except Exception as e:
                    self.logger.warning(f"Could not read legacy file: {e}")
            
            if not content:
                self.logger.info("No legacy CodeReviewerProjectMemory.md found to migrate")
                await self._mark_migration_complete("no_legacy_data")
                return
            
            self.logger.info(f"Migrating legacy data from {legacy_source}")
            await self._process_legacy_content(content)
            await self._mark_migration_complete(legacy_source)
            
        except Exception as e:
            self.logger.error(f"Legacy data migration failed: {e}")

    async def _process_legacy_content(self, content: str) -> None:
        """Process legacy content and import into v0.3 memory system."""
        lines = content.split('\n')
        current_pr = None
        current_section = None
        current_content = []
        
        for line in lines:
            # Detect PR sections
            if line.startswith('### PR #'):
                # Save previous section if exists
                if current_pr and current_section and current_content:
                    await self._import_legacy_section(current_pr, current_section, '\n'.join(current_content))
                
                # Start new PR
                current_pr = line.strip()
                current_section = None
                current_content = []
                
            # Detect subsections
            elif line.startswith('#### ') and current_pr:
                # Save previous section if exists
                if current_section and current_content:
                    await self._import_legacy_section(current_pr, current_section, '\n'.join(current_content))
                
                # Start new section
                current_section = line[5:].strip()  # Remove "#### "
                current_content = []
                
            # Collect content
            elif current_pr and current_section:
                current_content.append(line)
        
        # Don't forget the last section
        if current_pr and current_section and current_content:
            await self._import_legacy_section(current_pr, current_section, '\n'.join(current_content))

    async def _import_legacy_section(self, pr: str, section: str, content: str) -> None:
        """Import a legacy section into v0.3 memory system."""
        if not self.memory or not content.strip():
            return
        
        # Categorize based on section type
        memory_type = "semantic"  # Default
        importance = 0.7
        tags = ["legacy_import", "code_review"]
        
        # Extract PR number for tagging
        pr_match = pr.split('#')
        if len(pr_match) > 1:
            pr_number = pr_match[1].split(':')[0]
            tags.append(f"pr_{pr_number}")
        
        # Categorize by section type
        section_lower = section.lower()
        if any(keyword in section_lower for keyword in ['what i learned', 'insights', 'architectural']):
            memory_type = "semantic"
            importance = 0.8
            tags.append("insights")
        elif any(keyword in section_lower for keyword in ['patterns discovered', 'design patterns']):
            memory_type = "procedural"
            importance = 0.9
            tags.extend(["patterns", "design"])
        elif any(keyword in section_lower for keyword in ['security', 'vulnerabilities']):
            memory_type = "semantic"
            importance = 0.95
            tags.append("security")
        elif any(keyword in section_lower for keyword in ['patterns to watch', 'recommendations']):
            memory_type = "procedural"
            importance = 0.85
            tags.extend(["recommendations", "watch_patterns"])
        elif any(keyword in section_lower for keyword in ['test', 'coverage']):
            memory_type = "semantic"
            importance = 0.75
            tags.append("testing")
        
        # Store in memory
        formatted_content = f"Legacy Import - {pr}\n\n## {section}\n\n{content.strip()}"
        
        await self.memory.remember_long_term(
            content=formatted_content,
            memory_type=memory_type,
            tags=tags,
            importance=importance
        )

    async def _mark_migration_complete(self, source: str) -> None:
        """Mark the migration as completed."""
        if self.memory:
            await self.memory.remember_long_term(
                content=f"Legacy CodeReviewerProjectMemory.md migration completed. Source: {source}",
                memory_type="episodic",
                tags=["migration", "legacy_import", "completed"],
                importance=0.6
            )

    async def execute_task(self, task: Dict[str, Any]) -> TaskOutcome:
        """Execute a code review task."""
        start_time = datetime.now()
        task_type = task.get('type', 'code_review')

        try:
            if task_type == 'review_files':
                result = await self._review_files_task(task)
            elif task_type == 'learn_from_feedback':
                result = await self._learn_from_feedback_task(task)
            elif task_type == 'analyze_patterns':
                result = await self._analyze_patterns_task(task)
            else:
                result = await self._generic_review_task(task)

            duration = (datetime.now() - start_time).total_seconds()

            return TaskOutcome(
                success=True,
                task_id=self.current_task_id or "unknown",
                task_type=task_type,
                steps_taken=result.get('steps', []),
                duration_seconds=duration,
                lessons_learned=result.get('lessons', "Code review completed successfully")
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.exception(f"Code review task failed: {e}")

            return TaskOutcome(
                success=False,
                task_id=self.current_task_id or "unknown",
                task_type=task_type,
                steps_taken=[],
                duration_seconds=duration,
                error=str(e),
                lessons_learned=f"Failed due to: {e}"
            )

    async def _review_files_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Review a list of files with adaptive scoring."""
        files = task.get('files', [])
        pr_author = task.get('author', 'unknown')

        if not files:
            return {"steps": ["No files provided"], "lessons": "No files to review"}

        steps = []

        # Step 1: Run standard code review
        steps.append("Running standard code analysis")
        if not self.review_engine:
            raise ValueError("Review engine not initialized")
        review_result = await self.review_engine.review_files(files)

        # Step 2: Apply adaptive scoring based on patterns
        steps.append("Applying adaptive scoring based on learned patterns")
        adapted_result = await self._apply_adaptive_scoring(review_result, pr_author, files)

        # Step 3: Generate contextual recommendations
        steps.append("Generating contextual recommendations")
        recommendations = await self._generate_contextual_recommendations(
            adapted_result, pr_author, files
        )

        # Step 4: Store review in memory
        steps.append("Storing review results in memory")
        await self._store_review_in_memory(adapted_result, pr_author, files)

        # Step 5: Update patterns
        steps.append("Updating learned patterns")
        await self._update_patterns_from_review(adapted_result, pr_author, files)

        return {
            "steps": steps,
            "review_result": adapted_result.to_dict(),
            "recommendations": recommendations,
            "lessons": f"Reviewed {len(files)} files with adaptive scoring"
        }

    async def _apply_adaptive_scoring(
        self,
        review_result: ReviewResult,
        author: str,
        files: List[str]
    ) -> ReviewResult:
        """Apply adaptive scoring based on learned patterns."""
        if not self.config.get("adaptive_scoring", True):
            return review_result

        # Get developer pattern
        dev_pattern = self.developer_patterns.get(author)

        for file_review in review_result.file_reviews:
            module_pattern = self.module_patterns.get(file_review.file_path)

            # Adjust issue priorities based on patterns
            for issue in file_review.issues:
                original_severity = issue.severity

                # Developer-specific adjustments
                if dev_pattern:
                    if issue.rule_id in dev_pattern.ignored_rules:
                        # Developer consistently ignores this rule
                        issue.severity = max(1, issue.severity - 1)
                    elif issue.rule_id in dev_pattern.common_issues:
                        # Developer frequently has this issue
                        issue.severity = min(5, issue.severity + 1)

                # Module-specific adjustments
                if module_pattern:
                    if issue.rule_id in module_pattern.frequent_issues:
                        freq = module_pattern.frequent_issues[issue.rule_id]
                        if freq > 5:  # Frequent issue in this module
                            issue.severity = min(5, issue.severity + 1)

                # Remember the adjustment
                if issue.severity != original_severity and self.memory:
                    await self.memory.remember_short_term(
                        f"Adjusted severity for {issue.rule_id} from {original_severity} to {issue.severity} "
                        f"based on patterns for {author} in {file_review.file_path}",
                        tags=["adaptive_scoring", "pattern", author],
                        importance=0.6
                    )

        return review_result

    async def _generate_contextual_recommendations(
        self,
        review_result: ReviewResult,
        author: str,
        files: List[str]
    ) -> List[str]:
        """Generate contextual recommendations based on patterns."""
        recommendations = list(review_result.recommendations)  # Start with standard ones

        # Developer-specific recommendations
        dev_pattern = self.developer_patterns.get(author)
        if dev_pattern:
            # Check for recurring issues
            for rule_id, count in dev_pattern.common_issues.items():
                if count >= self.config.get("min_feedback_for_pattern", 3):
                    recommendations.append(
                        f"Consider reviewing the '{rule_id}' pattern - you've had this issue {count} times recently"
                    )

            # Suggest preferred patterns
            for pattern in dev_pattern.preferred_patterns[:3]:  # Top 3
                recommendations.append(f"Consider applying the '{pattern}' pattern you've used successfully before")

        # Module-specific recommendations
        for file_path in files:
            module_pattern = self.module_patterns.get(file_path)
            if module_pattern:
                # Security hotspot warning
                if file_path in module_pattern.security_hotspots:
                    recommendations.append(f"Extra security attention needed for {file_path} - known security hotspot")

                # Complexity trend warning
                if len(module_pattern.complexity_trends) >= 3:
                    recent_trend = sum(module_pattern.complexity_trends[-3:]) / 3
                    if recent_trend > 15:  # High complexity
                        recommendations.append(f"Consider refactoring {file_path} - complexity trending upward")

        return recommendations

    async def _store_review_in_memory(
        self,
        review_result: ReviewResult,
        author: str,
        files: List[str]
    ) -> None:
        """Store the review results in long-term memory."""
        # Store overall review
        review_summary = (
            f"Code review for {author}: {len(files)} files, "
            f"{review_result.summary.issues_found} issues found, "
            f"status: {review_result.status.value}, "
            f"score: {review_result.overall_score}"
        )

        if self.memory:
            await self.memory.remember_long_term(
                content=review_summary,
                memory_type="episodic",
                tags=["code_review", "completed", author] + [Path(f).stem for f in files[:3]],
                importance=0.8
            )

        # Store specific insights
        if self.memory:
            for file_review in review_result.file_reviews:
                if file_review.issues:
                    issue_summary = f"File {file_review.file_path}: {len(file_review.issues)} issues"
                    await self.memory.remember_long_term(
                        content=issue_summary,
                        memory_type="semantic",
                        tags=["file_review", Path(file_review.file_path).stem, author],
                        importance=0.6
                    )

    async def _update_patterns_from_review(
        self,
        review_result: ReviewResult,
        author: str,
        files: List[str]
    ) -> None:
        """Update learned patterns based on the review."""
        if not self.config.get("pattern_tracking_enabled", True):
            return

        # Update developer pattern
        if author not in self.developer_patterns:
            self.developer_patterns[author] = DeveloperPattern(developer=author)

        dev_pattern = self.developer_patterns[author]
        dev_pattern.last_reviewed = datetime.now()

        # Update module patterns
        for file_review in review_result.file_reviews:
            file_path = file_review.file_path

            if file_path not in self.module_patterns:
                self.module_patterns[file_path] = ModulePattern(module_path=file_path)

            module_pattern = self.module_patterns[file_path]
            module_pattern.last_reviewed = datetime.now()

            # Track complexity
            complexity = file_review.metrics.get('lines_of_code', 0) / 10  # Simple complexity metric
            module_pattern.complexity_trends.append(complexity)
            if len(module_pattern.complexity_trends) > 10:
                module_pattern.complexity_trends = module_pattern.complexity_trends[-10:]  # Keep last 10

            # Track frequent issues
            for issue in file_review.issues:
                if issue.rule_id not in module_pattern.frequent_issues:
                    module_pattern.frequent_issues[issue.rule_id] = 0
                module_pattern.frequent_issues[issue.rule_id] += 1

                # Track security hotspots
                if issue.category == IssueCategory.SECURITY and issue.severity >= 4:
                    if file_path not in module_pattern.security_hotspots:
                        module_pattern.security_hotspots.append(file_path)

        # Store patterns in long-term memory
        await self._persist_patterns_to_memory(author, files)

    async def _persist_patterns_to_memory(self, author: str, files: List[str]) -> None:
        """Persist updated patterns to long-term memory."""
        # Store developer pattern
        if author in self.developer_patterns:
            pattern = self.developer_patterns[author]
            pattern_content = (
                f"developer_pattern:\nDeveloper: {author}\n"
                f"Common issues: {dict(list(pattern.common_issues.items())[:5])}\n"
                f"Ignored rules: {list(pattern.ignored_rules)[:5]}\n"
                f"Last reviewed: {pattern.last_reviewed}"
            )

            if self.memory:
                await self.memory.remember_long_term(
                    content=pattern_content,
                    memory_type="semantic",
                    tags=["pattern", "developer", author],
                    importance=0.7
                )

        # Store module patterns
        for file_path in files:
            if file_path in self.module_patterns:
                pattern = self.module_patterns[file_path]
                pattern_content = (
                    f"module_pattern:\nModule: {file_path}\n"
                    f"Frequent issues: {dict(list(pattern.frequent_issues.items())[:5])}\n"
                    f"Complexity trend: {pattern.complexity_trends[-3:] if pattern.complexity_trends else []}\n"
                    f"Security hotspots: {len(pattern.security_hotspots) > 0}\n"
                    f"Last reviewed: {pattern.last_reviewed}"
                )

                if self.memory:
                    await self.memory.remember_long_term(
                        content=pattern_content,
                        memory_type="semantic",
                        tags=["pattern", "module", Path(file_path).stem],
                        importance=0.7
                    )

    async def _learn_from_feedback_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from human feedback on previous reviews."""
        feedback_data = task.get('feedback', [])

        steps = []
        learned_patterns = 0

        for feedback in feedback_data:
            steps.append(f"Processing feedback for issue {feedback.get('issue_id', 'unknown')}")

            # Create feedback record
            review_feedback = ReviewFeedback(
                issue_id=feedback.get('issue_id', ''),
                issue_type=feedback.get('issue_type', ''),
                category=feedback.get('category', ''),
                rule_id=feedback.get('rule_id', ''),
                developer=feedback.get('developer', ''),
                module=feedback.get('module', ''),
                file_path=feedback.get('file_path', ''),
                accepted=feedback.get('accepted', True),
                feedback_reason=feedback.get('reason')
            )

            # Update patterns based on feedback
            await self._update_patterns_from_feedback(review_feedback)
            learned_patterns += 1

            # Store feedback in memory
            feedback_content = (
                f"Review feedback: {review_feedback.rule_id} "
                f"{'accepted' if review_feedback.accepted else 'rejected'} "
                f"by {review_feedback.developer} "
                f"for {review_feedback.file_path}"
            )

            if self.memory:
                await self.memory.remember_long_term(
                    content=feedback_content,
                    memory_type="episodic",
                    tags=["feedback", "learning", review_feedback.developer, review_feedback.rule_id],
                    importance=0.9  # High importance for learning
                )

        steps.append(f"Updated patterns based on {learned_patterns} feedback items")

        return {
            "steps": steps,
            "learned_patterns": learned_patterns,
            "lessons": f"Learned from {len(feedback_data)} feedback items"
        }

    async def _update_patterns_from_feedback(self, feedback: ReviewFeedback) -> None:
        """Update patterns based on human feedback."""
        if not self.config.get("learning_enabled", True):
            return

        # Update developer patterns
        if feedback.developer not in self.developer_patterns:
            self.developer_patterns[feedback.developer] = DeveloperPattern(developer=feedback.developer)

        dev_pattern = self.developer_patterns[feedback.developer]

        if feedback.accepted:
            # Issue was accepted - track as common issue
            if feedback.rule_id not in dev_pattern.common_issues:
                dev_pattern.common_issues[feedback.rule_id] = 0
            dev_pattern.common_issues[feedback.rule_id] += 1
        else:
            # Issue was rejected - track as ignored rule
            dev_pattern.ignored_rules.add(feedback.rule_id)

            # Remove from common issues if it was there
            if feedback.rule_id in dev_pattern.common_issues:
                dev_pattern.common_issues[feedback.rule_id] = max(
                    0, dev_pattern.common_issues[feedback.rule_id] - 1
                )

        # Store the learning
        if self.memory:
            await self.memory.remember_long_term(
                content=f"Learned: {feedback.developer} {'accepts' if feedback.accepted else 'rejects'} {feedback.rule_id}",
                memory_type="procedural",
                tags=["learning", "pattern", feedback.developer, feedback.rule_id],
                importance=0.8
            )

    async def _analyze_patterns_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current patterns and generate insights."""
        steps = []
        insights = []

        # Analyze developer patterns
        steps.append("Analyzing developer patterns")
        for dev, pattern in self.developer_patterns.items():
            if len(pattern.common_issues) >= 3:
                top_issue = max(pattern.common_issues.items(), key=lambda x: x[1])
                insights.append(f"{dev} frequently has {top_issue[0]} issues ({top_issue[1]} times)")

        # Analyze module patterns
        steps.append("Analyzing module patterns")
        for module, pattern in self.module_patterns.items():
            if len(pattern.frequent_issues) >= 3:
                top_issue = max(pattern.frequent_issues.items(), key=lambda x: x[1])
                insights.append(f"{Path(module).name} frequently has {top_issue[0]} issues ({top_issue[1]} times)")

        # Store insights
        steps.append("Storing pattern analysis insights")
        if self.memory:
            for insight in insights:
                await self.memory.remember_long_term(
                    content=f"Pattern insight: {insight}",
                    memory_type="semantic",
                    tags=["insight", "pattern", "analysis"],
                    importance=0.7
                )

        return {
            "steps": steps,
            "insights": insights,
            "developer_patterns": len(self.developer_patterns),
            "module_patterns": len(self.module_patterns),
            "lessons": f"Analyzed patterns for {len(self.developer_patterns)} developers and {len(self.module_patterns)} modules"
        }

    async def _generic_review_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic review tasks."""
        description = task.get('description', 'Generic code review task')

        # Remember starting the task
        if self.memory:
            await self.memory.remember_short_term(
                f"Starting generic code review: {description}",
                tags=["task_start", "generic_review"],
                importance=0.5
            )

        return {
            "steps": ["Processed generic review task"],
            "lessons": "Completed generic review task"
        }

    async def get_developer_insights(self, developer: str) -> Dict[str, Any]:
        """Get insights about a specific developer's patterns."""
        if developer not in self.developer_patterns:
            return {"message": f"No pattern data for {developer}"}

        pattern = self.developer_patterns[developer]

        return {
            "developer": developer,
            "common_issues": dict(sorted(pattern.common_issues.items(), key=lambda x: x[1], reverse=True)[:5]),
            "ignored_rules": list(pattern.ignored_rules)[:5],
            "preferred_patterns": pattern.preferred_patterns[:5],
            "last_reviewed": pattern.last_reviewed.isoformat() if pattern.last_reviewed else None,
            "total_reviews": sum(pattern.common_issues.values())
        }

    async def get_module_insights(self, module_path: str) -> Dict[str, Any]:
        """Get insights about a specific module's patterns."""
        if module_path not in self.module_patterns:
            return {"message": f"No pattern data for {module_path}"}

        pattern = self.module_patterns[module_path]

        return {
            "module": module_path,
            "frequent_issues": dict(sorted(pattern.frequent_issues.items(), key=lambda x: x[1], reverse=True)[:5]),
            "complexity_trend": pattern.complexity_trends[-5:] if pattern.complexity_trends else [],
            "is_security_hotspot": module_path in pattern.security_hotspots,
            "last_reviewed": pattern.last_reviewed.isoformat() if pattern.last_reviewed else None,
            "total_issues": sum(pattern.frequent_issues.values())
        }

    async def can_handle_task(self, task_description: str) -> bool:
        """Check if this agent can handle a specific task."""
        review_keywords = [
            "review", "code review", "check code", "analyze code",
            "security review", "quality check", "lint", "style check"
        ]

        return any(keyword in task_description.lower() for keyword in review_keywords)


# Example usage and testing
async def test_code_reviewer_v03():
    """Test the Code Reviewer V0.3 agent."""
    print("\n" + "="*60)
    print("Testing Code Reviewer V0.3 Agent")
    print("="*60)

    # Create and initialize agent
    reviewer = CodeReviewerV03()

    try:
        await reviewer.initialize()

        # Test 1: Review files
        print("\n📋 Test 1: Review Files")
        task_id = await reviewer.start_task("Review Python files for quality and security")

        review_task = {
            "type": "review_files",
            "files": ["test_file.py", "another_file.py"],  # Dummy files for testing
            "author": "test_developer"
        }

        outcome = await reviewer.execute_task(review_task)
        await reviewer.learn_from_outcome(outcome)

        # Test 2: Learn from feedback
        print("\n📚 Test 2: Learn from Feedback")
        feedback_task = {
            "type": "learn_from_feedback",
            "feedback": [
                {
                    "issue_id": "issue_1",
                    "rule_id": "E501",  # Line too long
                    "developer": "test_developer",
                    "file_path": "test_file.py",
                    "accepted": False,
                    "reason": "Team prefers longer lines for readability"
                },
                {
                    "issue_id": "issue_2",
                    "rule_id": "F401",  # Unused import
                    "developer": "test_developer",
                    "file_path": "test_file.py",
                    "accepted": True,
                    "reason": "Good catch, removed unused import"
                }
            ]
        }

        outcome = await reviewer.execute_task(feedback_task)
        await reviewer.learn_from_outcome(outcome)

        # Test 3: Analyze patterns
        print("\n🔍 Test 3: Analyze Patterns")
        analysis_task = {"type": "analyze_patterns"}
        outcome = await reviewer.execute_task(analysis_task)
        await reviewer.learn_from_outcome(outcome)

        # Test 4: Get insights
        print("\n💡 Test 4: Get Developer Insights")
        insights = await reviewer.get_developer_insights("test_developer")
        print(f"Developer insights: {insights}")

        print(f"\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        await reviewer.shutdown()


if __name__ == "__main__":
    # Run tests if executed directly
    asyncio.run(test_code_reviewer_v03())
