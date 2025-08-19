from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Tuple  # type: ignore
)

from ..shared.error_handling import ErrorHandler
import json
import os
import subprocess

"""
System Design Reviewer Core - Main implementation for architectural review

Coordinates AST parsing, change analysis, documentation updates, and ADR generation
to provide comprehensive architectural review capabilities.
"""

from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# --------------------------------------------------------------------------- #
# Import shared modules from Enhanced Separation architecture
# We try three strategies to ensure compatibility across:
#   1. Installed package / production environment  -> absolute imports
#   2. In-repo execution (editable install / tests) -> relative ``..shared`` imports
#   3. Local fallback stubs                         -> ``fallbacks`` module
# --------------------------------------------------------------------------- #
try:
    # 1) Absolute imports (e.g. `python -m gadugi.system_design_reviewer`)
    from shared.github_operations import GitHubOperations
    from shared.state_management import StateManager
    from shared.error_handling import (
        ErrorHandler,
        ErrorCategory,
        ErrorSeverity)
    from shared.task_tracking import TaskTracker
except ImportError:  # pragma: no cover – fall through to relative/fallback
    try:
        # 2) Relative imports when executed inside repository package layout
        from ..shared.github_operations import GitHubOperations
        from ..shared.state_management import StateManager
        from ..shared.error_handling import (
            ErrorHandler,
            ErrorCategory,
            ErrorSeverity)
        from ..shared.task_tracking import TaskTracker
    except ImportError:
        # 3) Final fallback – use lightweight stub implementations
        print(
            "Warning: Enhanced-Separation shared modules not available, "
            "using local fallback implementations"
        )
        from .fallbacks import (  # type: ignore
            GitHubOperations,
            StateManager,
            ErrorHandler,
            ErrorCategory,
            ErrorSeverity,
            TaskTracker)

from .ast_parser import (
    ASTParserFactory, ArchitecturalChange, ImpactLevel
)
from .documentation_manager import DocumentationManager
from .adr_generator import ADRGenerator

class ReviewStatus(Enum):
    """Status of a design review"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ReviewResult:
    """Result of a system design review"""
    pr_number: str
    status: ReviewStatus
    architectural_impact: ImpactLevel
    changes_detected: List[ArchitecturalChange]
    documentation_updates: List[str]
    adrs_generated: List[str]
    review_comments: List[str]
    performance_metrics: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'changes_detected': [
                {
                    **asdict(change),
                    'change_type': change.change_type.value,
                    'impact_level': change.impact_level.value,
                    'element': {
                        **asdict(change.element),
                        'element_type': change.element.element_type.value
                    }
                }
                for change in self.changes_detected
            ]
        }

class SystemDesignReviewer:
    """Main System Design Review Agent implementation"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the system design reviewer"""
        self.config = config or {}

        # Initialize shared modules from Enhanced Separation architecture
        self.github_ops = GitHubOperations(task_id=getattr(self, 'task_id', None))
        self.state_manager = SystemDesignStateManager()
        self.error_handler = ErrorHandler("system-design-reviewer")
        self.task_tracker = TaskTracker("system-design-reviewer")

        # Initialize specialized components
        self.ast_parser_factory = ASTParserFactory()
        self.documentation_manager = DocumentationManager()
        self.adr_generator = ADRGenerator()

        # Configuration
        self.max_pr_size = self.config.get('max_pr_size', 1000)  # max files to analyze
        self.analysis_timeout = self.config.get('analysis_timeout', 300)  # 5 minutes
        self.enable_adr_generation = self.config.get('enable_adr', True)
        self.enable_doc_updates = self.config.get('enable_doc_updates', True)

        # Metrics
        self.performance_metrics = {
            'reviews_completed': 0,
            'average_review_time': 0,
            'accuracy_rate': 0,
            'adrs_generated': 0
        }

    def review_pr(self, pr_number: str, force_adr: bool = False,
                  update_architecture: bool = True) -> ReviewResult:
        """Main entry point for PR review"""
        start_time = datetime.now()

        try:
            # Update task status
            self.task_tracker.create_task(
                f"review_pr_{pr_number}",
                f"Review PR #{pr_number} for architectural changes",
                priority="high"  # type: ignore
            )
            self.task_tracker.update_task_status(f"review_pr_{pr_number}", "in_progress")

            # Get PR information
            pr_info = self._get_pr_info(pr_number)
            if not pr_info:
                raise ValueError(f"Could not retrieve PR #{pr_number}")

            # Analyze changes
            changes = self._analyze_pr_changes(pr_number, pr_info)

            # Assess overall impact
            overall_impact = self._assess_overall_impact(changes)

            # Generate documentation updates
            doc_updates = []
            if update_architecture and self.enable_doc_updates:
                doc_updates = self._update_documentation(changes, pr_info)

            # Generate ADRs if needed
            adrs_generated = []
            if self.enable_adr_generation:
                adrs_generated = self._generate_adrs(changes, pr_info, force_adr)

            # Generate review comments
            review_comments = self._generate_review_comments(changes, overall_impact)

            # Post review to GitHub
            self._post_github_review(pr_number, overall_impact, changes,
                                   doc_updates, adrs_generated, review_comments)

            # Create result
            end_time = datetime.now()
            review_time = (end_time - start_time).total_seconds()

            result = ReviewResult(
                pr_number=pr_number,
                status=ReviewStatus.COMPLETED,
                architectural_impact=overall_impact,
                changes_detected=changes,
                documentation_updates=doc_updates,
                adrs_generated=adrs_generated,
                review_comments=review_comments,
                performance_metrics={
                    'review_time_seconds': review_time,
                    'files_analyzed': len(pr_info.get('changed_files', [])),
                    'changes_detected': len(changes)
                },
                timestamp=end_time
            )

            # Update metrics and state
            self._update_metrics(result)
            self.state_manager.save_review_result(result)
            self.task_tracker.update_task_status(f"review_pr_{pr_number}", "completed")

            return result

        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.PROCESS_EXECUTION,
                severity=ErrorSeverity.HIGH,
                context={'pr_number': pr_number}
            )

            # Create failure result
            result = ReviewResult(
                pr_number=pr_number,
                status=ReviewStatus.FAILED,
                architectural_impact=ImpactLevel.LOW,
                changes_detected=[],
                documentation_updates=[],
                adrs_generated=[],
                review_comments=[f"Review failed: {str(e)}"],
                performance_metrics={},
                timestamp=datetime.now()
            )

            self.task_tracker.update_task_status(f"review_pr_{pr_number}", "failed")
            return result

    def _get_pr_info(self, pr_number: str) -> Dict[str, Any]:
        """Get PR information from GitHub"""
        try:
            # Use GitHub CLI to get PR details
            result = self.github_ops.get_pr_details(pr_number)  # type: ignore

            # Get changed files
            changed_files = self._get_changed_files(pr_number)
            result['changed_files'] = changed_files

            return result

        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.GITHUB_API,
                severity=ErrorSeverity.HIGH,
                context={'pr_number': pr_number}
            )
            return {}

    def _get_changed_files(self, pr_number: str) -> List[str]:
        """Get list of changed files in the PR"""
        try:
            cmd = f"gh pr diff {pr_number} --name-only"
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split('\n') if f.strip()]
            else:
                print(f"Error getting changed files: {result.stderr}")
                return []

        except Exception as e:
            print(f"Error getting changed files: {e}")
            return []

    def _analyze_pr_changes(self, pr_number: str, pr_info: Dict[str, Any]) -> List[ArchitecturalChange]:
        """Analyze architectural changes in the PR"""
        all_changes = []
        changed_files = pr_info.get('changed_files', [])

        # Filter for supported file types
        supported_extensions = self.ast_parser_factory.get_supported_extensions()
        analyzable_files = [
            f for f in changed_files
            if any(f.endswith(ext) for ext in supported_extensions)
        ]

        if len(analyzable_files) > self.max_pr_size:
            print(f"Warning: PR has {len(analyzable_files)} files, analyzing first {self.max_pr_size}")
            analyzable_files = analyzable_files[:self.max_pr_size]

        for file_path in analyzable_files:
            try:
                changes = self._analyze_file_changes(file_path, pr_number)
                all_changes.extend(changes)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                continue

        return all_changes

    def _analyze_file_changes(self, file_path: str, pr_number: str) -> List[ArchitecturalChange]:
        """Analyze changes in a specific file"""
        parser = self.ast_parser_factory.get_parser(file_path)
        if not parser:
            return []

        try:
            # Get old version of file (before PR)
            old_content = self._get_file_content_at_base(file_path, pr_number)
            old_elements = []
            if old_content:
                # Write to temp file for parsing
                temp_file = f"/tmp/{Path(file_path).name}.old"
                with open(temp_file, 'w') as f:
                    f.write(old_content)
                old_elements = parser.parse_file(temp_file)
                os.unlink(temp_file)

            # Get new version of file (current PR state)
            if os.path.exists(file_path):
                new_elements = parser.parse_file(file_path)
            else:
                # File was deleted
                new_elements = []

            # Analyze changes
            changes = parser.analyze_changes(old_elements, new_elements)

            # Add file context to changes
            for change in changes:
                change.affected_components.append(file_path)

            return changes

        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return []

    def _get_file_content_at_base(self, file_path: str, pr_number: str) -> Optional[str]:
        """Get file content at the base branch of the PR"""
        try:
            # Get PR base branch
            cmd = f"gh pr view {pr_number} --json baseRefName"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)

            if result.returncode != 0:
                return None

            pr_data = json.loads(result.stdout)
            base_branch = pr_data.get('baseRefName', 'main')

            # Get file content at base
            cmd = f"git show {base_branch}:{file_path}"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout
            else:
                # File might not exist in base branch
                return None

        except Exception as e:
            print(f"Error getting base content for {file_path}: {e}")
            return None

    def _assess_overall_impact(self, changes: List[ArchitecturalChange]) -> ImpactLevel:
        """Assess overall architectural impact of all changes"""
        if not changes:
            return ImpactLevel.LOW

        # Count impact levels
        impact_counts = {level: 0 for level in ImpactLevel}
        for change in changes:
            impact_counts[change.impact_level] += 1

        # Determine overall impact
        if impact_counts[ImpactLevel.CRITICAL] > 0:
            return ImpactLevel.CRITICAL
        elif impact_counts[ImpactLevel.HIGH] > 2:
            return ImpactLevel.HIGH
        elif impact_counts[ImpactLevel.HIGH] > 0 or impact_counts[ImpactLevel.MEDIUM] > 3:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW

    def _update_documentation(self, changes: List[ArchitecturalChange],
                            pr_info: Dict[str, Any]) -> List[str]:
        """Update architecture documentation based on changes"""
        try:
            return self.documentation_manager.update_architecture_doc(changes, pr_info)
        except Exception as e:
            print(f"Error updating documentation: {e}")
            return []

    def _generate_adrs(self, changes: List[ArchitecturalChange], pr_info: Dict[str, Any],
                      force: bool = False) -> List[str]:
        """Generate Architecture Decision Records for significant changes"""
        try:
            significant_changes = [
                change for change in changes
                if change.requires_adr or force
            ]

            if not significant_changes and not force:
                return []

            return self.adr_generator.generate_adrs(significant_changes, pr_info)
        except Exception as e:
            print(f"Error generating ADRs: {e}")
            return []

    def _generate_review_comments(self, changes: List[ArchitecturalChange],
                                overall_impact: ImpactLevel) -> List[str]:
        """Generate review comments for the PR"""
        comments = []

        # Overall assessment
        impact_descriptions = {
            ImpactLevel.LOW: "No significant architectural impact detected",
            ImpactLevel.MEDIUM: "Moderate architectural changes - review recommended",
            ImpactLevel.HIGH: "Significant architectural changes - careful review required",
            ImpactLevel.CRITICAL: "Critical architectural changes - thorough review essential"
        }

        comments.append(f"**Architectural Impact**: {overall_impact.value.title()}")
        comments.append(impact_descriptions[overall_impact])
        comments.append("")

        # Group changes by type
        changes_by_type = {}
        for change in changes:
            change_type = change.change_type
            if change_type not in changes_by_type:
                changes_by_type[change_type] = []
            changes_by_type[change_type].append(change)

        # Generate comments for each change type
        for change_type, type_changes in changes_by_type.items():
            if not type_changes:
                continue

            comments.append(f"### {change_type.value.title()} Elements")

            for change in type_changes:
                element = change.element
                comments.append(f"- **{element.element_type.value}** `{element.name}` at {element.location}")

                if change.design_implications:
                    comments.append(f"  - Impact: {', '.join(change.design_implications)}")

                if change.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
                    comments.append(f"  - ⚠️ {change.impact_level.value.title()} impact - review required")

            comments.append("")

        return comments

    def _post_github_review(self, pr_number: str, overall_impact: ImpactLevel,
                          changes: List[ArchitecturalChange], doc_updates: List[str],
                          adrs_generated: List[str], review_comments: List[str]):
        """Post the review to GitHub"""
        try:
            # Determine review action
            if overall_impact == ImpactLevel.CRITICAL:
                review_action = "REQUEST_CHANGES"
            elif overall_impact in [ImpactLevel.HIGH, ImpactLevel.MEDIUM]:
                review_action = "COMMENT"
            else:
                review_action = "APPROVE"

            # Build review body
            review_body = self._build_review_body(
                overall_impact, changes, doc_updates, adrs_generated, review_comments
            )

            # Post review using GitHub operations
            self.github_ops.post_pr_review(pr_number, review_action, review_body)  # type: ignore

        except Exception as e:
            print(f"Error posting GitHub review: {e}")

    def _build_review_body(self, overall_impact: ImpactLevel,
                          changes: List[ArchitecturalChange], doc_updates: List[str],
                          adrs_generated: List[str], review_comments: List[str]) -> str:
        """Build the review body content"""
        sections = [
            "## System Design Review Summary",
            "",
            f"**Architectural Impact**: {overall_impact.value.title()}",
            "",
            "*Note: This review was conducted by an AI agent on behalf of the repository owner.*",
            ""
        ]

        # Add main review comments
        sections.extend(review_comments)

        # Add documentation updates section
        if doc_updates:
            sections.extend([
                "### Documentation Updates",
                "",
                "The following documentation was updated:",
                ""
            ])
            sections.extend([f"- {update}" for update in doc_updates])
            sections.append("")

        # Add ADR section
        if adrs_generated:
            sections.extend([
                "### Architecture Decision Records",
                "",
                "Generated ADRs for this change:",
                ""
            ])
            sections.extend([f"- {adr}" for adr in adrs_generated])
            sections.append("")

        # Add component interaction analysis if significant changes
        if overall_impact in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            affected_components = set()
            for change in changes:
                affected_components.update(change.affected_components)

            if affected_components:
                sections.extend([
                    "### Affected Components",
                    "",
                    "This change affects the following components:",
                    ""
                ])
                sections.extend([f"- `{comp}`" for comp in sorted(affected_components)])
                sections.append("")

        return "\n".join(sections)

    def _update_metrics(self, result: ReviewResult):
        """Update performance metrics"""
        self.performance_metrics['reviews_completed'] += 1

        # Update average review time
        review_time = result.performance_metrics.get('review_time_seconds', 0)
        current_avg = self.performance_metrics['average_review_time']
        total_reviews = self.performance_metrics['reviews_completed']

        new_avg = ((current_avg * (total_reviews - 1)) + review_time) / total_reviews
        self.performance_metrics['average_review_time'] = new_avg

        # Update ADR count
        self.performance_metrics['adrs_generated'] += len(result.adrs_generated)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()

    def analyze_pr(self, pr_number: str, **kwargs) -> ReviewResult:
        """Alias for review_pr for CLI compatibility"""
        return self.review_pr(pr_number, **kwargs)

class SystemDesignStateManager(StateManager):  # type: ignore
    """State manager for System Design Review Agent"""

    def __init__(self):
        super().__init__(
            state_dir=Path(".github/workflow-states/system-design-reviewer"),
            task_id="system-design-reviewer"
        )

    def get_default_state(self) -> Dict[str, Any]:
        """Get default state structure"""
        return {
            'active_reviews': {},
            'completed_reviews': [],
            'performance_metrics': {
                'total_reviews': 0,
                'average_review_time': 0,
                'accuracy_rate': 0
            },
            'configuration': {
                'enable_adr_generation': True,
                'enable_doc_updates': True,
                'max_pr_size': 1000
            }
        }

    def save_review_result(self, result: ReviewResult) -> bool:
        """Save a review result to state"""
        try:
            state = self.load_state()

            # Update completed reviews
            state['completed_reviews'].append(result.to_dict())

            # Keep only last 100 reviews
            if len(state['completed_reviews']) > 100:
                state['completed_reviews'] = state['completed_reviews'][-100:]

            # Remove from active reviews if present
            if result.pr_number in state['active_reviews']:
                del state['active_reviews'][result.pr_number]

            return self.save_state(state)

        except Exception as e:
            print(f"Error saving review result: {e}")
            return False
