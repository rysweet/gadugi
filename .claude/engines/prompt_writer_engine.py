#!/usr/bin/env python3
"""Prompt Writer Engine - Core logic for generating structured prompts.
This provides programmatic access to prompt generation capabilities.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


class PromptWriterEngine:
    """Engine for generating structured development prompts."""

    def __init__(self) -> None:
        self.template_structure = {
            "overview": "Brief description of the feature and its purpose",
            "problem_statement": "Clear description of what problem this solves",
            "requirements": {
                "functional": "List of what the feature should do",
                "technical": "Implementation constraints, dependencies, patterns",
            },
            "implementation_plan": {
                "phase1": "Research and Setup",
                "phase2": "Core Implementation",
                "phase3": "Testing and Validation",
                "phase4": "Documentation and Integration",
            },
            "success_criteria": "Measurable outcomes that define completion",
            "workflow_steps": [
                "Create GitHub issue",
                "Create feature branch",
                "Research and plan",
                "Implement core functionality",
                "Add comprehensive tests",
                "Update documentation",
                "Create pull request",
                "Address code review feedback",
                "Merge when approved",
            ],
        }

    def generate_prompt(
        self,
        task_description: str,
        context: dict | None = None,
    ) -> dict:
        """Generate a structured prompt based on task description.

        Args:
            task_description: High-level description of what needs to be done
            context: Optional additional context about the project/codebase

        Returns:
            Dictionary containing the structured prompt content

        """
        context = context or {}

        # Analyze the task to extract key information
        analysis = self._analyze_task(task_description)

        # Generate each section of the prompt
        return {
            "title": analysis["title"],
            "overview": self._generate_overview(analysis),
            "problem_statement": self._generate_problem_statement(analysis),
            "requirements": self._generate_requirements(analysis),
            "implementation_plan": self._generate_implementation_plan(analysis),
            "success_criteria": self._generate_success_criteria(analysis),
            "workflow_steps": self.template_structure["workflow_steps"],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "task_type": analysis["task_type"],
                "complexity": analysis["complexity"],
            },
        }

    def _analyze_task(self, task_description: str) -> dict:
        """Analyze task description to extract key information."""
        return {
            "original_task": task_description,
            "title": self._extract_title(task_description),
            "task_type": self._determine_task_type(task_description),
            "complexity": self._estimate_complexity(task_description),
            "components": self._identify_components(task_description),
            "keywords": self._extract_keywords(task_description),
        }

    def _extract_title(self, task_description: str) -> str:
        """Extract a clean title from task description."""
        # Remove common prefixes and clean up
        title = task_description.strip()
        title = re.sub(
            r"^(implement|add|create|build|fix|enhance|update)\s+",
            "",
            title,
            flags=re.IGNORECASE,
        )

        # Capitalize first letter and important words
        if title:
            title = title[0].upper() + title[1:]
            # Capitalize after spaces for better formatting
            words = title.split()
            title = " ".join(word.capitalize() if len(word) > 2 else word for word in words)

        return f"{title} Implementation" if not title.endswith("Implementation") else title

    def _determine_task_type(self, task_description: str) -> str:
        """Determine the type of task based on description."""
        description_lower = task_description.lower()

        if any(word in description_lower for word in ["implement", "add", "create", "build"]):
            return "feature_implementation"
        if any(word in description_lower for word in ["fix", "bug", "error", "issue"]):
            return "bug_fix"
        if any(word in description_lower for word in ["enhance", "improve", "optimize", "update"]):
            return "enhancement"
        if any(
            word in description_lower
            for word in ["unit test", "testing", "test coverage", "add tests"]
        ):
            return "testing"
        if any(word in description_lower for word in ["doc", "document", "readme"]):
            return "documentation"
        return "general_development"

    def _estimate_complexity(self, task_description: str) -> str:
        """Estimate task complexity based on description."""
        description_lower = task_description.lower()
        complexity_indicators = {
            "high": [
                "system",
                "architecture",
                "database",
                "authentication",
                "security",
                "integration",
                "api",
            ],
            "medium": ["feature", "component", "service", "interface", "workflow"],
            "low": ["fix", "update", "simple", "basic", "small"],
        }

        for level, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                return level

        return "medium"  # Default

    def _identify_components(self, task_description: str) -> list[str]:
        """Identify likely components/technologies mentioned in description."""
        description_lower = task_description.lower()
        components = []

        # Common technologies and components
        tech_keywords = {
            "web": ["web", "html", "css", "javascript", "frontend"],
            "api": ["api", "rest", "endpoint", "service"],
            "database": ["database", "db", "sql", "mongodb", "postgres"],
            "auth": ["auth", "authentication", "login", "security"],
            "testing": ["test", "testing", "unit test", "integration"],
            "ui": ["ui", "interface", "component", "widget"],
            "backend": ["backend", "server", "service", "api"],
        }

        for component, keywords in tech_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                components.append(component)

        return components

    def _extract_keywords(self, task_description: str) -> list[str]:
        """Extract important keywords from the task description."""
        # Simple keyword extraction - remove common words
        common_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        words = re.findall(r"\w+", task_description.lower())
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        return keywords[:10]  # Limit to 10 keywords

    def _generate_overview(self, analysis: dict) -> str:
        """Generate overview section based on analysis."""
        task_type = analysis["task_type"]
        title = analysis["title"]

        if task_type == "feature_implementation":
            return f"This prompt guides the implementation of {title.lower()}. The feature will enhance the application's capabilities and provide users with improved functionality."
        if task_type == "bug_fix":
            return f"This prompt addresses a specific issue requiring {title.lower()}. The fix will resolve the problem and restore expected functionality."
        if task_type == "enhancement":
            return f"This prompt focuses on {title.lower()} to improve existing functionality. The enhancement will provide better performance and user experience."
        return f"This prompt provides guidance for {title.lower()}. The work will contribute to the overall quality and functionality of the application."

    def _generate_problem_statement(self, analysis: dict) -> str:
        """Generate problem statement based on analysis."""
        task_type = analysis["task_type"]
        original_task = analysis["original_task"]

        if task_type == "feature_implementation":
            return f"The application currently lacks {original_task.lower()}. Users need this functionality to accomplish their goals effectively."
        if task_type == "bug_fix":
            return f"There is a reported issue: {original_task}. This problem affects user experience and needs to be resolved."
        return f"The current state requires improvement: {original_task}. This work will address the identified need."

    def _generate_requirements(self, analysis: dict) -> dict:
        """Generate requirements sections based on analysis."""
        task_type = analysis["task_type"]
        components = analysis["components"]
        analysis["complexity"]

        functional_reqs = []
        technical_reqs = []

        if task_type == "feature_implementation":
            functional_reqs = [
                "Clear user interface for the new functionality",
                "Proper input validation and error handling",
                "Integration with existing application features",
                "Appropriate user feedback and notifications",
            ]
            technical_reqs = [
                "Follow existing code patterns and architecture",
                "Maintain backward compatibility",
                "Implement proper error handling and logging",
                "Include comprehensive unit and integration tests",
            ]
        elif task_type == "bug_fix":
            functional_reqs = [
                "Resolve the identified issue completely",
                "Restore expected functionality",
                "Prevent regression of the same issue",
                "Maintain all existing functionality",
            ]
            technical_reqs = [
                "Identify and fix root cause",
                "Add tests to prevent regression",
                "Update documentation if necessary",
                "Minimal impact on existing code",
            ]
        else:
            functional_reqs = [
                "Achieve the specified improvement goals",
                "Maintain existing functionality",
                "Provide measurable benefits",
                "User-friendly implementation",
            ]
            technical_reqs = [
                "Follow established coding standards",
                "Implement appropriate testing",
                "Document changes and decisions",
                "Consider performance implications",
            ]

        # Add component-specific requirements
        if "database" in components:
            technical_reqs.append("Database schema changes with migration scripts")
        if "api" in components:
            technical_reqs.append("RESTful API design with proper HTTP status codes")
        if "auth" in components:
            technical_reqs.append("Security best practices and authentication flows")

        return {"functional": functional_reqs, "technical": technical_reqs}

    def _generate_implementation_plan(self, analysis: dict) -> dict:
        """Generate implementation plan based on analysis."""
        complexity = analysis["complexity"]
        analysis["task_type"]

        if complexity == "high":
            return {
                "phase1": [
                    "Research existing patterns and similar implementations",
                    "Analyze system architecture and integration points",
                    "Create detailed technical design document",
                    "Set up development environment and dependencies",
                ],
                "phase2": [
                    "Implement core data models and business logic",
                    "Create API endpoints and service layer",
                    "Implement user interface components",
                    "Add proper error handling and validation",
                ],
                "phase3": [
                    "Write comprehensive unit tests for all components",
                    "Create integration tests for API endpoints",
                    "Perform manual testing and user acceptance testing",
                    "Test edge cases and error scenarios",
                ],
                "phase4": [
                    "Update API documentation and code comments",
                    "Create user documentation and examples",
                    "Update deployment and configuration guides",
                    "Prepare rollback procedures",
                ],
            }
        if complexity == "medium":
            return {
                "phase1": [
                    "Analyze requirements and existing code",
                    "Design solution approach and components",
                    "Identify integration points and dependencies",
                ],
                "phase2": [
                    "Implement main functionality",
                    "Add input validation and error handling",
                    "Create user interface elements",
                ],
                "phase3": [
                    "Write unit tests for new functionality",
                    "Test integration with existing features",
                    "Verify error handling and edge cases",
                ],
                "phase4": [
                    "Update relevant documentation",
                    "Add code comments and examples",
                    "Verify deployment procedures",
                ],
            }
        # low complexity
        return {
            "phase1": ["Review existing code and identify changes needed"],
            "phase2": [
                "Implement the required changes",
                "Add basic validation and error handling",
            ],
            "phase3": [
                "Add tests to verify the changes work correctly",
                "Test integration with existing functionality",
            ],
            "phase4": [
                "Update documentation as needed",
                "Add comments explaining the changes",
            ],
        }

    def _generate_success_criteria(self, analysis: dict) -> list[str]:
        """Generate success criteria based on analysis."""
        task_type = analysis["task_type"]
        complexity = analysis["complexity"]

        base_criteria = [
            "All tests pass without errors",
            "Code follows project style guidelines",
            "No breaking changes to existing functionality",
            "Pull request approved by code reviewer",
        ]

        if task_type == "feature_implementation":
            base_criteria.extend(
                [
                    "New functionality works as specified",
                    "User interface is intuitive and accessible",
                    "Feature integrates seamlessly with existing application",
                ],
            )
        elif task_type == "bug_fix":
            base_criteria.extend(
                [
                    "Reported issue is completely resolved",
                    "Fix does not introduce new issues",
                    "Root cause has been addressed",
                ],
            )

        if complexity in ["medium", "high"]:
            base_criteria.extend(
                [
                    "Comprehensive documentation is updated",
                    "Performance impact is acceptable",
                    "Security considerations have been addressed",
                ],
            )

        return base_criteria

    def format_as_markdown(self, prompt_data: dict) -> str:
        """Format the prompt data as a markdown document."""
        md = f"# {prompt_data['title']}\n\n"

        md += f"## Overview\n{prompt_data['overview']}\n\n"

        md += f"## Problem Statement\n{prompt_data['problem_statement']}\n\n"

        md += "## Requirements\n\n"
        md += "### Functional Requirements\n"
        for req in prompt_data["requirements"]["functional"]:
            md += f"- {req}\n"
        md += "\n### Technical Requirements\n"
        for req in prompt_data["requirements"]["technical"]:
            md += f"- {req}\n"
        md += "\n"

        md += "## Implementation Plan\n\n"
        for phase, tasks in prompt_data["implementation_plan"].items():
            phase_num = phase.replace("phase", "Phase ")
            md += f"### {phase_num}\n"
            if isinstance(tasks, list):
                for task in tasks:
                    md += f"- {task}\n"
            else:
                md += f"- {tasks}\n"
            md += "\n"

        md += "## Success Criteria\n"
        for criterion in prompt_data["success_criteria"]:
            md += f"- {criterion}\n"
        md += "\n"

        md += "## Workflow Steps\n"
        for i, step in enumerate(prompt_data["workflow_steps"], 1):
            md += f"{i}. {step}\n"
        md += "\n"

        # Add metadata as comment
        metadata = prompt_data["metadata"]
        md += f"<!-- Generated: {metadata['generated_at']}, "
        md += f"Type: {metadata['task_type']}, "
        md += f"Complexity: {metadata['complexity']} -->\n"

        return md


def generate_prompt_for_task(task_description: str, save_to_file: bool = False) -> dict:
    """Main function to generate a prompt for a given task.

    Args:
        task_description: Description of the task
        save_to_file: Whether to save the prompt to a file

    Returns:
        Dictionary containing the generated prompt and metadata

    """
    engine = PromptWriterEngine()

    # Generate the structured prompt
    prompt_data = engine.generate_prompt(task_description)

    # Format as markdown
    markdown_content = engine.format_as_markdown(prompt_data)

    result = {
        "success": True,
        "prompt_data": prompt_data,
        "markdown": markdown_content,
        "suggested_filename": _generate_filename(task_description),
    }

    # Optionally save to file
    if save_to_file:
        filename = result["suggested_filename"]
        file_path = Path("prompts") / filename
        file_path.parent.mkdir(exist_ok=True)

        with open(file_path, "w") as f:
            f.write(markdown_content)

        result["saved_to"] = str(file_path)

    return result


def _generate_filename(task_description: str) -> str:
    """Generate a filename based on task description."""
    # Clean the description to create a filename
    clean_desc = re.sub(r"[^\w\s-]", "", task_description.lower())
    clean_desc = re.sub(r"\s+", "-", clean_desc.strip())

    # Limit length and add prefix
    if len(clean_desc) > 50:
        clean_desc = clean_desc[:50]

    # Determine prefix based on content
    if any(word in clean_desc for word in ["fix", "bug", "error"]):
        prefix = "fix"
    elif any(word in clean_desc for word in ["enhance", "improve", "update"]):
        prefix = "enhance"
    else:
        prefix = "implement"

    return f"{prefix}-{clean_desc}.md"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sys.exit(1)

    task_description = " ".join(sys.argv[1:])
    result = generate_prompt_for_task(task_description, save_to_file=False)

    if result["success"]:
        pass
    else:
        pass
