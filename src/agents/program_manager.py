from datetime import timedelta
import json
import os
import re
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys

"""
Program Manager Agent Implementation

Manages project health through issue lifecycle management, priority tracking,
and documentation maintenance.
"""


# Add parent directory to path for imports

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

try:
    from memory_utils.agent_interface import (  # type: ignore[import]
        AgentMemoryInterface as BaseAgentMemoryInterface,
    )

    AgentMemoryInterface = BaseAgentMemoryInterface
except ImportError:
    # Fallback if memory_utils not available
    class AgentMemoryInterface:
        def __init__(self, agent_id: str, agent_type: str):
            self.agent_id = agent_id
            self.agent_type = agent_type

        def get_project_context(self) -> Dict:
            return {}

        def record_project_memory(self, category: str, content: str):
            print(f"[Memory] {category}: {content}")

        def record_agent_memory(self, category: str, content: str):
            print(f"[Agent Memory] {category}: {content}")


class IssueStage(Enum):
    """Issue lifecycle stages as defined in issue #44"""

    UNLABELED = "unlabeled"
    IDEA = "idea"
    DRAFT = "draft"
    REQUIREMENTS_REVIEW = "requirements-review"
    DESIGN_READY = "design-ready"
    DESIGN_REVIEW = "design-review"
    READY = "ready"
    FUTURE = "future"
    BUG = "bug"


@dataclass
class Issue:
    """Represents a GitHub issue"""

    number: int
    title: str
    body: str
    labels: List[str]
    state: str
    author: str
    created_at: str
    updated_at: str


class ProgramManager:
    """Program Manager agent for project orchestration"""

    def __init__(self, agent_id: str = "pm-001"):
        self.agent_id = agent_id
        self.memory = AgentMemoryInterface(agent_id, "program-manager")
        self.lifecycle_labels = [
            stage.value for stage in IssueStage if stage != IssueStage.UNLABELED
        ]

    def run_gh_command(self, args: List[str]) -> Tuple[bool, str]:
        """Execute GitHub CLI command and return success status and output"""
        try:
            result = subprocess.run(
                ["gh"] + args, capture_output=True, text=True, check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"

    def parse_issue_from_gh(self, issue_data: str) -> Optional[Issue]:
        """Parse issue data from gh issue view output"""
        lines = issue_data.strip().split("\n")
        if not lines:
            return None

        # Parse the header fields
        fields = {}
        for line in lines:
            if line.startswith("--"):
                break
            if "\t" in line:
                key, value = line.split("\t", 1)
                fields[key.rstrip(":")] = value

        # Extract body (everything after --)
        body_start = next(
            (i for i, line in enumerate(lines) if line.startswith("--")), -1
        )
        body = "\n".join(lines[body_start + 1 :]) if body_start >= 0 else ""

        # Parse labels
        labels = []
        if "labels" in fields and fields["labels"]:
            labels = [label.strip() for label in fields["labels"].split(",")]

        return Issue(
            number=int(fields.get("number", 0)),
            title=fields.get("title", ""),
            body=body,
            labels=labels,
            state=fields.get("state", "OPEN"),
            author=fields.get("author", ""),
            created_at=fields.get("created", ""),
            updated_at=fields.get("updated", ""),
        )

    def get_issues_by_label(self, label: Optional[str] = None) -> List[Issue]:
        """Get all issues with a specific label (or unlabeled if label is None)"""
        args = [
            "issue",
            "list",
            "--json",
            "number,title,body,labels,state,author,createdAt,updatedAt",
        ]
        if label:
            args.extend(["--label", label])
        else:
            # Get all issues and filter unlabeled ones
            pass

        success, output = self.run_gh_command(args)
        if not success:
            print(f"Failed to get issues: {output}")
            return []

        try:
            issues_data = json.loads(output)
            issues = []

            for data in issues_data:
                # Convert label objects to strings
                label_names = [label["name"] for label in data.get("labels", [])]

                # Filter unlabeled if needed
                if label is None and label_names:
                    continue

                issue = Issue(
                    number=data["number"],
                    title=data["title"],
                    body=data.get("body", ""),
                    labels=label_names,
                    state=data["state"],
                    author=data.get("author", {}).get("login", ""),
                    created_at=data.get("createdAt", ""),
                    updated_at=data.get("updatedAt", ""),
                )
                issues.append(issue)

            return issues
        except json.JSONDecodeError:
            print("Failed to parse JSON output")
            return []

    def get_current_lifecycle_stage(self, issue: Issue) -> Optional[IssueStage]:
        """Determine the current lifecycle stage of an issue"""
        lifecycle_labels_in_issue = [
            label for label in issue.labels if label in self.lifecycle_labels
        ]

        if not lifecycle_labels_in_issue:
            return IssueStage.UNLABELED

        # Should only have one lifecycle label
        if len(lifecycle_labels_in_issue) > 1:
            print(
                f"Warning: Issue #{issue.number} has multiple lifecycle labels: {lifecycle_labels_in_issue}"
            )

        label = lifecycle_labels_in_issue[0]
        return IssueStage(label)

    def classify_issue(self, issue: Issue) -> IssueStage:
        """Classify an unlabeled issue into appropriate stage"""
        # Check if it's a bug
        if "bug" in issue.labels or self._looks_like_bug(issue):
            return IssueStage.BUG

        # Check if it's well-structured
        if self._is_well_structured(issue):
            return IssueStage.DRAFT
        else:
            return IssueStage.IDEA

    def _looks_like_bug(self, issue: Issue) -> bool:
        """Determine if an issue looks like a bug report"""
        bug_keywords = [
            "bug",
            "error",
            "crash",
            "broken",
            "fix",
            "issue",
            "problem",
            "fail",
        ]
        text = (issue.title + " " + issue.body).lower()
        return any(keyword in text for keyword in bug_keywords)

    def _is_well_structured(self, issue: Issue) -> bool:
        """Check if an issue is well-structured enough to be a draft"""
        # Must have a body
        if not issue.body or len(issue.body.strip()) < 50:
            return False

        # Check for structure indicators
        structure_indicators = [
            "##",
            "###",
            "- ",
            "* ",
            "1.",
            "requirements:",
            "description:",
            "acceptance criteria:",
        ]
        body_lower = issue.body.lower()

        structure_count = sum(
            1 for indicator in structure_indicators if indicator in body_lower
        )
        return structure_count >= 2

    def update_issue_label(
        self, issue_number: int, add_label: str, remove_label: Optional[str] = None
    ) -> bool:
        """Update issue labels"""
        args = ["issue", "edit", str(issue_number), "--add-label", add_label]
        if remove_label:
            args.extend(["--remove-label", remove_label])

        success, output = self.run_gh_command(args)
        if not success:
            print(f"Failed to update issue #{issue_number}: {output}")
        return success

    def triage_unlabeled_issues(self) -> Dict[str, int]:
        """Triage all unlabeled issues"""
        print("Starting issue triage...")
        stats = {"total": 0, "idea": 0, "draft": 0, "bug": 0, "error": 0}

        # Get all unlabeled issues
        unlabeled = self.get_issues_by_label(None)
        stats["total"] = len(unlabeled)

        print(f"Found {len(unlabeled)} unlabeled issues")

        for issue in unlabeled:
            print(f"\nTriaging issue #{issue.number}: {issue.title}")

            # Skip if it already has lifecycle labels
            if any(label in self.lifecycle_labels for label in issue.labels):
                print("  Skipping - already has lifecycle label")
                continue

            # Classify the issue
            stage = self.classify_issue(issue)
            print(f"  Classified as: {stage.value}")

            # Update the label
            if self.update_issue_label(issue.number, stage.value):
                stats[stage.value] = stats.get(stage.value, 0) + 1
                print(f"  ✓ Added label: {stage.value}")
            else:
                stats["error"] += 1
                print("  ✗ Failed to add label")

        # Record in memory
        summary = f"Triaged {stats['total']} issues: {stats['idea']} ideas, {stats['draft']} drafts, {stats['bug']} bugs"
        self.memory.record_agent_memory("issue_triage", summary)

        return stats

    def convert_ideas_to_drafts(self) -> Dict[str, int]:
        """Convert well-formed ideas to drafts"""
        print("\nConverting ideas to drafts...")
        stats = {"total": 0, "converted": 0, "error": 0}

        # Get all ideas
        ideas = self.get_issues_by_label("idea")
        stats["total"] = len(ideas)

        print(f"Found {len(ideas)} issues labeled 'idea'")

        for issue in ideas:
            print(f"\nReviewing issue #{issue.number}: {issue.title}")

            # Check if it can be promoted to draft
            if self._is_well_structured(issue):
                print("  Issue is well-structured, converting to draft")

                if self.update_issue_label(issue.number, "draft", "idea"):
                    stats["converted"] += 1
                    print("  ✓ Converted to draft")
                else:
                    stats["error"] += 1
                    print("  ✗ Failed to convert")
            else:
                print("  Issue needs more structure, keeping as idea")

        # Record in memory
        summary = (
            f"Reviewed {stats['total']} ideas, converted {stats['converted']} to drafts"
        )
        self.memory.record_agent_memory("idea_conversion", summary)

        return stats

    def structure_idea(self, issue: Issue) -> str:
        """Structure an unstructured idea into a draft format"""
        structured = f"""# {issue.title}

## Problem Statement
{self._extract_problem(issue.body)}

## Proposed Solution
{self._extract_solution(issue.body)}

## Success Criteria
- TODO: Define measurable success criteria
- TODO: Add acceptance criteria

## Implementation Notes
- TODO: Add technical considerations
- TODO: Note any dependencies

---
*Note: This issue was structured by the Program Manager agent*
"""
        return structured

    def _extract_problem(self, body: str) -> str:
        """Extract problem statement from issue body"""
        # Simple extraction - can be enhanced with NLP
        lines = body.split("\n")
        problem_lines = []

        for line in lines[:5]:  # Look at first 5 lines
            if line.strip():
                problem_lines.append(line.strip())

        return (
            "\n".join(problem_lines)
            if problem_lines
            else "TODO: Define the problem this issue addresses"
        )

    def _extract_solution(self, body: str) -> str:
        """Extract solution from issue body"""
        # Look for solution keywords
        solution_keywords = ["solution", "fix", "implement", "add", "create", "should"]
        lines = body.split("\n")

        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in solution_keywords):
                # Return this line and next few
                return "\n".join(lines[i : i + 3])

        return "TODO: Define the proposed solution"

    def enforce_single_lifecycle_label(self) -> Dict[str, int]:
        """Ensure each issue has only one lifecycle label"""
        print("\nEnforcing single lifecycle label rule...")
        stats = {"total": 0, "fixed": 0, "error": 0}

        # Get all issues
        success, output = self.run_gh_command(
            ["issue", "list", "--json", "number,labels", "--limit", "1000"]
        )
        if not success:
            print(f"Failed to get issues: {output}")
            return stats

        try:
            all_issues = json.loads(output)
            stats["total"] = len(all_issues)

            for issue_data in all_issues:
                labels = [label["name"] for label in issue_data.get("labels", [])]
                lifecycle_labels_in_issue = [
                    label for label in labels if label in self.lifecycle_labels
                ]

                if len(lifecycle_labels_in_issue) > 1:
                    print(
                        f"\nIssue #{issue_data['number']} has multiple lifecycle labels: {lifecycle_labels_in_issue}"
                    )

                    # Keep the most advanced stage
                    stages_order = [
                        IssueStage.IDEA,
                        IssueStage.DRAFT,
                        IssueStage.REQUIREMENTS_REVIEW,
                        IssueStage.DESIGN_READY,
                        IssueStage.DESIGN_REVIEW,
                        IssueStage.READY,
                    ]

                    kept_label = None
                    for stage in reversed(stages_order):
                        if stage.value in lifecycle_labels_in_issue:
                            kept_label = stage.value
                            break

                    if kept_label:
                        # Remove all lifecycle labels except the kept one
                        for label in lifecycle_labels_in_issue:
                            if label != kept_label:
                                self.run_gh_command(
                                    [
                                        "issue",
                                        "edit",
                                        str(issue_data["number"]),
                                        "--remove-label",
                                        label,
                                    ]
                                )
                        stats["fixed"] += 1
                        print(f"  ✓ Kept only: {kept_label}")

        except json.JSONDecodeError:
            stats["error"] += 1

        return stats

    def run_full_triage(self):
        """Run complete issue triage process"""
        print("=== Running Full Issue Triage ===\n")

        # 1. Triage unlabeled issues
        triage_stats = self.triage_unlabeled_issues()

        # 2. Convert mature ideas to drafts
        conversion_stats = self.convert_ideas_to_drafts()

        # 3. Enforce single label rule
        label_stats = self.enforce_single_lifecycle_label()

        # Summary
        print("\n=== Triage Summary ===")
        print(f"Unlabeled issues triaged: {triage_stats['total']}")
        print(f"Ideas converted to drafts: {conversion_stats['converted']}")
        print(f"Multi-label issues fixed: {label_stats['fixed']}")

        # Record summary in memory
        self.memory.record_agent_memory(
            "triage_summary",
            f"Full triage completed: {triage_stats['total']} triaged, "
            f"{conversion_stats['converted']} converted, {label_stats['fixed']} labels fixed",
        )

    def get_milestone_info(self) -> Dict[str, Any]:
        """Get information about project milestones"""
        success, output = self.run_gh_command(
            ["api", "/repos/{owner}/{repo}/milestones", "--jq", "."]
        )
        if not success:
            print(f"Failed to get milestones: {output}")
            return {}

        try:
            milestones = json.loads(output)
            milestone_info = {}

            for milestone in milestones:
                milestone_info[milestone["title"]] = {
                    "open_issues": milestone["open_issues"],
                    "closed_issues": milestone["closed_issues"],
                    "due_on": milestone.get("due_on"),
                    "description": milestone.get("description", ""),
                    "state": milestone["state"],
                }

            return milestone_info
        except json.JSONDecodeError:
            return {}

    def analyze_ready_issues(self) -> List[Dict[str, Any]]:
        """Analyze issues that are ready for implementation"""
        ready_issues = self.get_issues_by_label("ready")

        analysis = []
        for issue in ready_issues:
            # Check for blockers or dependencies mentioned
            has_blockers = any(
                word in issue.body.lower()
                for word in ["blocked", "depends on", "waiting for"]
            )

            # Estimate complexity based on description length and structure
            complexity = "low"
            if len(issue.body) > 1000:
                complexity = "high"
            elif len(issue.body) > 500:
                complexity = "medium"

            analysis.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "complexity": complexity,
                    "has_blockers": has_blockers,
                    "created_days_ago": self._days_since(issue.created_at),
                    "labels": issue.labels,
                }
            )

        # Sort by age and complexity
        analysis.sort(
            key=lambda x: (x["has_blockers"], x["complexity"], -x["created_days_ago"])
        )

        return analysis

    def _days_since(self, date_str: str) -> int:
        """Calculate days since a date string"""
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return (datetime.now(date.tzinfo) - date).days
        except Exception:
            return 0

    def update_project_priorities(self) -> bool:
        """Update project priorities in memory based on current state"""
        print("\n=== Updating Project Priorities ===")

        # Get milestone info
        milestones = self.get_milestone_info()

        # Analyze ready issues
        ready_issues = self.analyze_ready_issues()

        # Get issue distribution by stage
        stage_counts = {}
        for stage in IssueStage:
            if stage != IssueStage.UNLABELED:
                issues = self.get_issues_by_label(stage.value)
                stage_counts[stage.value] = len(issues)

        # Build priority list
        priorities = []
        priority_number = 1

        # Priority 1: Address any blockers
        blocked_ready = [issue for issue in ready_issues if issue["has_blockers"]]
        if blocked_ready:
            priorities.append(
                f"{priority_number}. **Unblock ready issues**: {len(blocked_ready)} issues blocked"
            )
            priority_number += 1

        # Priority 2: Complete ready issues (oldest/simplest first)
        unblocked_ready = [issue for issue in ready_issues if not issue["has_blockers"]]
        if unblocked_ready:
            top_ready = unblocked_ready[:3]
            ready_list = ", ".join([f"#{issue['number']}" for issue in top_ready])
            priorities.append(
                f"{priority_number}. **Implement ready issues**: {ready_list} (and {len(unblocked_ready) - 3} more)"
            )
            priority_number += 1

        # Priority 3: Move design-review to ready
        if stage_counts.get("design-review", 0) > 0:
            priorities.append(
                f"{priority_number}. **Complete design reviews**: {stage_counts['design-review']} issues awaiting review"
            )
            priority_number += 1

        # Priority 4: Process requirements-review
        if stage_counts.get("requirements-review", 0) > 0:
            priorities.append(
                f"{priority_number}. **Complete requirements reviews**: {stage_counts['requirements-review']} issues need review"
            )
            priority_number += 1

        # Priority 5: Structure ideas
        if stage_counts.get("idea", 0) > 5:
            priorities.append(
                f"{priority_number}. **Structure idea backlog**: {stage_counts['idea']} ideas need structuring"
            )
            priority_number += 1

        # Build priority content
        priority_content = f"""# Project Priorities
*Last Updated: {datetime.now().isoformat()}*
*Generated by: Program Manager Agent*

## Current Top Priorities

{chr(10).join(priorities)}

## Issue Pipeline Status
"""

        # Add pipeline status
        for stage in [
            IssueStage.IDEA,
            IssueStage.DRAFT,
            IssueStage.REQUIREMENTS_REVIEW,
            IssueStage.DESIGN_READY,
            IssueStage.DESIGN_REVIEW,
            IssueStage.READY,
        ]:
            count = stage_counts.get(stage.value, 0)
            priority_content += f"- **{stage.value}**: {count} issues\n"

        # Add milestone status
        if milestones:
            priority_content += "\n## Milestone Progress\n"
            for name, info in milestones.items():
                if info["state"] == "open":
                    total = info["open_issues"] + info["closed_issues"]
                    percent = (info["closed_issues"] / total * 100) if total > 0 else 0
                    priority_content += f"- **{name}**: {percent:.0f}% complete ({info['closed_issues']}/{total})"
                    if info["due_on"]:
                        priority_content += f" - Due: {info['due_on'][:10]}"
                    priority_content += "\n"

        # Add recommendations
        priority_content += "\n## Recommendations\n"

        if stage_counts.get("idea", 0) > stage_counts.get("ready", 0) * 2:
            priority_content += (
                "- ⚠️ **Idea backlog growing**: Consider dedicated grooming session\n"
            )

        if stage_counts.get("ready", 0) < 3:
            priority_content += "- ⚠️ **Low ready pipeline**: Focus on moving issues through review stages\n"

        old_ready = [issue for issue in ready_issues if issue["created_days_ago"] > 14]
        if old_ready:
            priority_content += f"- ⚠️ **Stale ready issues**: {len(old_ready)} issues ready for >2 weeks\n"

        # Write to memory
        try:
            # Create .memory/project directory if it doesn't exist
            memory_dir = os.path.join(
                os.path.dirname(__file__), "../../.memory/project"
            )
            os.makedirs(memory_dir, exist_ok=True)

            # Write priorities file
            priority_file = os.path.join(memory_dir, "priorities.md")
            with open(priority_file, "w") as f:
                f.write(priority_content)

            print(f"✓ Updated project priorities in {priority_file}")

            # Record in agent memory
            self.memory.record_agent_memory(
                "priority_update",
                f"Updated project priorities: {len(priorities)} top priorities, "
                f"{sum(stage_counts.values())} total issues in pipeline",
            )

            return True

        except Exception as e:
            print(f"✗ Failed to update priorities: {e}")
            return False

    def get_recent_merged_prs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recently merged pull requests"""
        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        success, output = self.run_gh_command(
            [
                "pr",
                "list",
                "--state",
                "merged",
                "--json",
                "number,title,body,mergedAt,author,labels",
                "--search",
                f"merged:>{since_date}",
            ]
        )

        if not success:
            print(f"Failed to get merged PRs: {output}")
            return []

        try:
            prs = json.loads(output)
            return prs
        except json.JSONDecodeError:
            return []

    def extract_features_from_pr(self, pr: Dict[str, Any]) -> List[str]:
        """Extract feature descriptions from a PR"""
        features = []

        # Look for feature indicators in title
        title = pr.get("title", "").lower()
        if any(
            word in title for word in ["add", "implement", "create", "feature", "new"]
        ):
            features.append(pr["title"])

        # Parse body for features
        body = pr.get("body", "")
        if body:
            lines = body.split("\n")
            for line in lines:
                line = line.strip()
                # Look for bullet points or numbered lists describing features
                if (
                    line.startswith("- ")
                    or line.startswith("* ")
                    or re.match(r"^\d+\.", line)
                ) and len(line) > 10:
                    features.append(line.lstrip("- *").lstrip("0123456789.").strip())

        return features[:3]  # Limit to top 3 features per PR

    def detect_new_agents(self) -> List[str]:
        """Detect new agents added to the system"""
        new_agents = []

        # Check .claude/agents directory
        agents_dir = os.path.join(os.path.dirname(__file__), "../../.claude/agents")
        if os.path.exists(agents_dir):
            for filename in os.listdir(agents_dir):
                if filename.endswith(".md") and filename != "template.md":
                    agent_name = filename[:-3]  # Remove .md extension

                    # Check if agent is mentioned in README
                    readme_path = os.path.join(
                        os.path.dirname(__file__), "../../README.md"
                    )
                    if os.path.exists(readme_path):
                        with open(readme_path, "r") as f:
                            readme_content = f.read().lower()
                            if agent_name not in readme_content:
                                new_agents.append(agent_name)

        return new_agents

    def update_readme(self) -> bool:
        """Update README.md with latest features and capabilities"""
        print("\n=== Updating README.md ===")

        readme_path = os.path.join(os.path.dirname(__file__), "../../README.md")
        if not os.path.exists(readme_path):
            print("✗ README.md not found")
            return False

        # Read current README
        with open(readme_path, "r") as f:
            readme_content = f.read()

        # Get recent features from PRs
        recent_prs = self.get_recent_merged_prs(days=14)
        new_features = []
        for pr in recent_prs:
            features = self.extract_features_from_pr(pr)
            for feature in features:
                new_features.append(f"- {feature} (PR #{pr['number']})")

        # Detect new agents
        new_agents = self.detect_new_agents()

        # Check if updates are needed
        updates_needed = False
        update_summary = []

        if new_features:
            print(f"Found {len(new_features)} new features from recent PRs")
            updates_needed = True
            update_summary.append(f"{len(new_features)} new features")

        if new_agents:
            print(f"Found {len(new_agents)} new agents not in README")
            updates_needed = True
            update_summary.append(f"{len(new_agents)} new agents")

        if not updates_needed:
            print("✓ README is up to date")
            return True

        # Create updated README content
        updated_readme = readme_content

        # Add new features section if needed
        if new_features and "## Recent Updates" not in readme_content:
            # Find where to insert (after main description, before first ##)
            lines = readme_content.split("\n")
            insert_index = 0

            for i, line in enumerate(lines):
                if line.startswith("##") and i > 5:  # Skip title area
                    insert_index = i
                    break

            recent_section = f"""## Recent Updates

{chr(10).join(new_features[:5])}

"""
            lines.insert(insert_index, recent_section)
            updated_readme = "\n".join(lines)

        # Update agents list if needed
        if new_agents:
            # Find agents section
            agents_section_start = updated_readme.find("## Available Agents")
            if agents_section_start == -1:
                agents_section_start = updated_readme.find("## Agents")

            if agents_section_start != -1:
                # Find next section
                next_section = updated_readme.find("\n##", agents_section_start + 1)
                if next_section == -1:
                    next_section = len(updated_readme)

                # Add new agents to the list
                for agent in new_agents:
                    agent_line = f"\n- **{agent}**: [Description needed]"

                    # Insert before the next section
                    insert_pos = next_section - 1
                    updated_readme = (
                        updated_readme[:insert_pos]
                        + agent_line
                        + updated_readme[insert_pos:]
                    )

        # Write updated README
        backup_path = readme_path + ".backup"
        try:
            # Create backup
            with open(backup_path, "w") as f:
                f.write(readme_content)

            # Write new content
            with open(readme_path, "w") as f:
                f.write(updated_readme)

            print(f"✓ Updated README.md with {', '.join(update_summary)}")

            # Record in memory
            self.memory.record_agent_memory(
                "readme_update", f"Updated README with {', '.join(update_summary)}"
            )

            return True

        except Exception as e:
            print(f"✗ Failed to update README: {e}")
            # Restore backup if exists
            if os.path.exists(backup_path):
                with open(backup_path, "r") as f:
                    backup_content = f.read()
                with open(readme_path, "w") as f:
                    f.write(backup_content)
            return False

    def run_full_maintenance(self):
        """Run complete project maintenance cycle"""
        print("=== Running Full Project Maintenance ===\n")

        # 1. Run issue triage
        self.run_full_triage()

        # 2. Update project priorities
        self.update_project_priorities()

        # 3. Update README
        self.update_readme()

        print("\n=== Maintenance Complete ===")

        # Record completion
        self.memory.record_agent_memory(
            "maintenance_complete",
            f"Completed full project maintenance cycle at {datetime.now().isoformat()}",
        )


if __name__ == "__main__":
    # Example usage
    import sys

    pm = ProgramManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "triage":
            pm.run_full_triage()
        elif command == "priorities":
            pm.update_project_priorities()
        elif command == "readme":
            pm.update_readme()
        elif command == "full":
            pm.run_full_maintenance()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: triage, priorities, readme, full")
    else:
        # Default: run full maintenance
        pm.run_full_maintenance()
