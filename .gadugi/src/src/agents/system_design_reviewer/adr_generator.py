"""
ADR Generator - Architecture Decision Record generation

Automatically generates Architecture Decision Records (ADRs) for significant
architectural changes detected in pull requests.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .ast_parser import ArchitecturalChange, ImpactLevel, ElementType  # type: ignore


@dataclass
class ADRData:
    """Data structure for an Architecture Decision Record"""

    number: int
    title: str
    date: datetime
    status: str  # Proposed, Accepted, Superseded, Deprecated
    context: str
    decision: str
    rationale: str
    consequences: List[str]
    alternatives: List[str]
    implementation_notes: str
    related_changes: List[str]
    pr_number: Optional[str] = None


class ADRGenerator:
    """Generates Architecture Decision Records for significant changes"""

    def __init__(self, adr_dir: str = "docs/adr"):
        self.adr_dir = Path(adr_dir)
        self.adr_dir.mkdir(parents=True, exist_ok=True)

        # ADR generation patterns
        self.decision_patterns = {
            "new_pattern": "Adoption of new architectural pattern",
            "framework_change": "Framework or technology stack change",
            "interface_change": "Public interface modification",
            "security_change": "Security architecture modification",
            "performance_change": "Performance architecture change",
            "integration_change": "External integration modification",
        }

    def generate_adrs(
        self, changes: List[ArchitecturalChange], pr_info: Dict[str, Any]
    ) -> List[str]:
        """Generate ADRs for significant architectural changes"""
        generated_adrs = []

        # Group changes by decision category
        decision_groups = self._group_changes_by_decision(changes)

        for decision_type, group_changes in decision_groups.items():
            if not group_changes:
                continue

            try:
                adr_data = self._create_adr_data(decision_type, group_changes, pr_info)
                adr_file = self._write_adr(adr_data)
                generated_adrs.append(adr_file)

            except Exception as e:
                print(f"Error generating ADR for {decision_type}: {e}")
                continue

        return generated_adrs

    def _group_changes_by_decision(
        self, changes: List[ArchitecturalChange]
    ) -> Dict[str, List[ArchitecturalChange]]:
        """Group changes by the type of architectural decision they represent"""
        groups = {decision_type: [] for decision_type in self.decision_patterns.keys()}

        for change in changes:
            # Only consider changes that require ADRs
            if not change.requires_adr:
                continue

            _element = change.element
            decision_type = self._classify_decision_type(change)

            if decision_type in groups:
                groups[decision_type].append(change)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def _classify_decision_type(self, change: ArchitecturalChange) -> str:
        """Classify what type of architectural decision a change represents"""
        element = change.element

        # Security-related changes
        security_indicators = [
            "auth",
            "security",
            "xpia",
            "defense",
            "audit",
            "permission",
        ]
        if any(indicator in element.name.lower() for indicator in security_indicators):
            return "security_change"

        # Performance-related changes
        if (
            element.is_async
            or "performance" in element.name.lower()
            or "parallel" in element.name.lower()
        ):
            return "performance_change"

        # Integration-related changes
        integration_indicators = ["github", "api", "webhook", "cli", "integration"]
        if any(
            indicator in element.name.lower() for indicator in integration_indicators
        ):
            return "integration_change"

        # Framework/technology changes
        framework_indicators = ["container", "docker", "pytest", "fastapi", "django"]
        if any(indicator in element.name.lower() for indicator in framework_indicators):
            return "framework_change"

        # Interface changes (public APIs)
        if (
            element.element_type in [ElementType.CLASS, ElementType.FUNCTION]
            and element.is_public
            and len(element.dependencies) > 3
        ):
            return "interface_change"

        # Pattern changes (architectural patterns)
        pattern_indicators = ["singleton", "factory", "observer", "decorator", "abc"]
        if any(pattern in element.patterns for pattern in pattern_indicators):
            return "new_pattern"

        # Default to interface change for significant modifications
        return "interface_change"

    def _create_adr_data(
        self,
        decision_type: str,
        changes: List[ArchitecturalChange],
        pr_info: Dict[str, Any],
    ) -> ADRData:
        """Create ADR data structure for a group of changes"""
        adr_number = self._get_next_adr_number()
        pr_number = pr_info.get("number", "Unknown")
        _pr_title = pr_info.get("title", "Untitled Change")

        # Generate title
        title = self._generate_title(decision_type, changes)

        # Generate context
        context = self._generate_context(decision_type, changes, pr_info)

        # Generate decision description
        decision = self._generate_decision(decision_type, changes)

        # Generate rationale
        rationale = self._generate_rationale(decision_type, changes)

        # Generate consequences
        consequences = self._generate_consequences(changes)

        # Generate alternatives
        alternatives = self._generate_alternatives(decision_type, changes)

        # Generate implementation notes
        implementation_notes = self._generate_implementation_notes(changes)

        # Generate related changes
        related_changes = self._generate_related_changes(changes, pr_info)

        return ADRData(
            number=adr_number,
            title=title,
            date=datetime.now(),
            status="Proposed",  # Initial status
            context=context,
            decision=decision,
            rationale=rationale,
            consequences=consequences,
            alternatives=alternatives,
            implementation_notes=implementation_notes,
            related_changes=related_changes,
            pr_number=pr_number,
        )

    def _get_next_adr_number(self) -> int:
        """Get the next ADR number"""
        existing_adrs = list(self.adr_dir.glob("ADR-*.md"))

        if not existing_adrs:
            return 1

        # Extract numbers from existing ADRs
        numbers = []
        for adr_file in existing_adrs:
            match = re.search(r"ADR-(\d+)", adr_file.name)
            if match:
                numbers.append(int(match.group(1)))

        return max(numbers) + 1 if numbers else 1

    def _generate_title(
        self, decision_type: str, changes: List[ArchitecturalChange]
    ) -> str:
        """Generate ADR title"""
        base_title = self.decision_patterns.get(decision_type, "Architectural Change")

        # Add specific details based on changes
        if len(changes) == 1:
            element_name = changes[0].element.name
            return f"{base_title}: {element_name}"
        else:
            # Multiple changes - use component or pattern name
            component_names = set()
            for change in changes:
                if change.element.parent_element:
                    component_names.add(change.element.parent_element)
                else:
                    component_names.add(change.element.name.split(".")[0])

            if len(component_names) == 1:
                return f"{base_title}: {list(component_names)[0]} Component"
            else:
                return f"{base_title}: Multiple Components"

    def _generate_context(
        self,
        decision_type: str,
        changes: List[ArchitecturalChange],
        pr_info: Dict[str, Any],
    ) -> str:
        """Generate context section"""
        pr_number = pr_info.get("number", "Unknown")
        pr_title = pr_info.get("title", "Untitled Change")

        context = f"This decision emerges from PR #{pr_number}: {pr_title}\n\n"

        # Add change summary
        context += "The following architectural changes were detected:\n"
        for change in changes:
            context += f"- {change.get_description()} at {change.element.location}\n"

        # Add impact assessment
        high_impact = [c for c in changes if c.impact_level == ImpactLevel.HIGH]
        critical_impact = [c for c in changes if c.impact_level == ImpactLevel.CRITICAL]

        if critical_impact:
            context += f"\n{len(critical_impact)} critical impact changes require architectural review.\n"
        elif high_impact:
            context += f"\n{len(high_impact)} high impact changes affect system architecture.\n"

        return context

    def _generate_decision(
        self, decision_type: str, changes: List[ArchitecturalChange]
    ) -> str:
        """Generate decision description"""
        decision_templates = {
            "new_pattern": "We will adopt the {pattern} architectural pattern for {component}.",
            "framework_change": "We will integrate {framework} into the system architecture.",
            "interface_change": "We will modify the public interface of {component} to {modification}.",
            "security_change": "We will implement {security_measure} to enhance system security.",
            "performance_change": "We will optimize {component} for improved performance characteristics.",
            "integration_change": "We will modify the integration with {external_system}.",
        }

        template = decision_templates.get(
            decision_type, "We will implement the following architectural change:"
        )

        # Extract specific details from changes
        details = self._extract_decision_details(decision_type, changes)

        try:
            return template.format(**details)
        except KeyError:
            # Fallback if template formatting fails
            return (
                "We will implement the following architectural changes:\n"
                + "\n".join([f"- {change.get_description()}" for change in changes])
            )

    def _extract_decision_details(
        self, decision_type: str, changes: List[ArchitecturalChange]
    ) -> Dict[str, str]:
        """Extract specific details for decision templating"""
        details = {}

        if decision_type == "new_pattern":
            patterns = set()
            components = set()
            for change in changes:
                patterns.update(change.element.patterns)
                components.add(change.element.name)

            details["pattern"] = (
                ", ".join(patterns) if patterns else "architectural pattern"
            )
            details["component"] = (
                ", ".join(list(components)[:3]) if components else "components"
            )

        elif decision_type == "framework_change":
            frameworks = set()
            for change in changes:
                if "container" in change.element.name.lower():
                    frameworks.add("containerization")
                elif "pytest" in change.element.name.lower():
                    frameworks.add("pytest testing framework")
                # Add more framework detection logic

            details["framework"] = (
                ", ".join(frameworks) if frameworks else "new framework"
            )

        elif decision_type == "interface_change":
            components = [change.element.name for change in changes]
            details["component"] = ", ".join(components[:3])
            details["modification"] = "support new functionality"

        elif decision_type == "security_change":
            security_measures = []
            for change in changes:
                if "auth" in change.element.name.lower():
                    security_measures.append("authentication mechanisms")
                elif "xpia" in change.element.name.lower():
                    security_measures.append("XPIA defense systems")

            details["security_measure"] = (
                ", ".join(security_measures)
                if security_measures
                else "security enhancements"
            )

        elif decision_type == "performance_change":
            components = [
                change.element.name for change in changes if change.element.is_async
            ]
            details["component"] = (
                ", ".join(components) if components else "system components"
            )

        elif decision_type == "integration_change":
            systems = []
            for change in changes:
                if "github" in change.element.name.lower():
                    systems.append("GitHub API")
                elif "api" in change.element.name.lower():
                    systems.append("external APIs")

            details["external_system"] = (
                ", ".join(systems) if systems else "external systems"
            )

        return details

    def _generate_rationale(
        self, decision_type: str, changes: List[ArchitecturalChange]
    ) -> str:
        """Generate rationale section"""
        rationale_templates = {
            "new_pattern": "This pattern provides better separation of concerns and improves maintainability.",
            "framework_change": "This framework integration enhances system capabilities and performance.",
            "interface_change": "These interface modifications are necessary to support new functionality while maintaining backward compatibility.",
            "security_change": "These security enhancements are critical for maintaining system integrity and protecting against threats.",
            "performance_change": "These performance optimizations are necessary to maintain system responsiveness and scalability.",
            "integration_change": "These integration changes improve system interoperability and external communication.",
        }

        base_rationale = rationale_templates.get(
            decision_type, "This change is necessary for system evolution."
        )

        # Add specific justifications from change implications
        implications = set()
        for change in changes:
            implications.update(change.design_implications)

        if implications:
            base_rationale += "\n\nSpecific benefits include:\n"
            for implication in sorted(implications):
                base_rationale += f"- {implication}\n"

        return base_rationale

    def _generate_consequences(self, changes: List[ArchitecturalChange]) -> List[str]:
        """Generate consequences (positive and negative)"""
        consequences = []

        # Positive consequences
        consequences.append("**Positive:**")
        consequences.append("- Improved architectural coherence")
        consequences.append("- Enhanced maintainability")

        # Add specific positive consequences based on change types
        async_changes = [c for c in changes if c.element.is_async]
        if async_changes:
            consequences.append("- Better concurrency and performance")

        pattern_changes = [c for c in changes if c.element.patterns]
        if pattern_changes:
            consequences.append("- Improved design pattern consistency")

        # Negative consequences
        consequences.append("")
        consequences.append("**Negative:**")
        consequences.append("- Increased initial complexity")
        consequences.append("- Potential learning curve for team members")

        # Add specific negative consequences
        if len(changes) > 5:
            consequences.append("- Significant refactoring effort required")

        high_impact_changes = [c for c in changes if c.impact_level == ImpactLevel.HIGH]
        if high_impact_changes:
            consequences.append("- Risk of introducing regressions")

        return consequences

    def _generate_alternatives(
        self, decision_type: str, changes: List[ArchitecturalChange]
    ) -> List[str]:
        """Generate alternatives considered"""
        _alternatives = []

        alternative_templates = {
            "new_pattern": [
                "Continue with existing implementation patterns",
                "Adopt a different architectural pattern",
                "Implement a hybrid approach combining multiple patterns",
            ],
            "framework_change": [
                "Maintain current technology stack",
                "Evaluate alternative frameworks",
                "Implement custom solution without external framework",
            ],
            "interface_change": [
                "Maintain current interface with deprecated methods",
                "Create entirely new interface while preserving old one",
                "Implement breaking change with migration guide",
            ],
            "security_change": [
                "Implement minimal security measures",
                "Use third-party security solutions",
                "Delay security improvements to future release",
            ],
            "performance_change": [
                "Accept current performance characteristics",
                "Implement different optimization approach",
                "Scale infrastructure instead of optimizing code",
            ],
            "integration_change": [
                "Maintain current integration approach",
                "Use different integration technology",
                "Implement custom integration solution",
            ],
        }

        return alternative_templates.get(
            decision_type,
            [
                "Maintain status quo",
                "Implement different approach",
                "Defer decision to future iteration",
            ],
        )

    def _generate_implementation_notes(self, changes: List[ArchitecturalChange]) -> str:
        """Generate implementation notes"""
        notes = "Implementation considerations:\n\n"

        # Add file-specific notes
        affected_files = set()
        for change in changes:
            file_path = change.element.location.split(":")[0]
            affected_files.add(file_path)

        if affected_files:
            notes += "**Affected Files:**\n"
            for file_path in sorted(affected_files):
                notes += f"- `{file_path}`\n"
            notes += "\n"

        # Add pattern-specific notes
        patterns = set()
        for change in changes:
            patterns.update(change.element.patterns)

        if patterns:
            notes += "**Architectural Patterns Involved:**\n"
            for pattern in sorted(patterns):
                notes += f"- {pattern}\n"
            notes += "\n"

        # Add testing considerations
        notes += "**Testing Requirements:**\n"
        notes += "- Unit tests for all modified components\n"
        notes += "- Integration tests for architectural changes\n"
        notes += "- Performance tests if applicable\n"

        return notes

    def _generate_related_changes(
        self, changes: List[ArchitecturalChange], pr_info: Dict[str, Any]
    ) -> List[str]:
        """Generate related changes references"""
        related = []

        pr_number = pr_info.get("number")
        if pr_number:
            related.append(f"PR #{pr_number}")

        # Add issue references if available
        pr_body = pr_info.get("body", "")
        issue_matches = re.findall(
            r"(?:closes|fixes|resolves)\s+#(\d+)", pr_body, re.IGNORECASE
        )
        for issue_num in issue_matches:
            related.append(f"Issue #{issue_num}")

        # Look for related ADRs (could be enhanced with actual ADR scanning)
        related.append("Previous ADRs: TBD")

        return related

    def _write_adr(self, adr_data: ADRData) -> str:
        """Write ADR to file"""
        filename = f"ADR-{adr_data.number:03d}-{self._slugify(adr_data.title)}.md"
        file_path = self.adr_dir / filename

        content = self._format_adr_content(adr_data)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)

    def _slugify(self, title: str) -> str:
        """Convert title to filename-safe slug"""
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r"[^\w\-_\.]", "-", title.lower())
        # Remove multiple consecutive hyphens
        slug = re.sub(r"-+", "-", slug)
        # Remove leading/trailing hyphens
        return slug.strip("-")

    def _format_adr_content(self, adr_data: ADRData) -> str:
        """Format ADR content according to standard template"""
        template = f"""# ADR-{adr_data.number:03d}: {adr_data.title}

**Date**: {adr_data.date.strftime('%Y-%m-%d')}
**Status**: {adr_data.status}
**Context**: PR #{adr_data.pr_number}

## Decision

{adr_data.decision}

## Rationale

{adr_data.rationale}

## Consequences

{chr(10).join(adr_data.consequences)}

## Alternatives Considered

{chr(10).join([f'- {alt}' for alt in adr_data.alternatives])}

## Implementation Notes

{adr_data.implementation_notes}

## Related Changes

{chr(10).join([f'- {ref}' for ref in adr_data.related_changes])}

---

*This ADR was automatically generated by the SystemDesignReviewer agent.*
*Generated on: {datetime.now().isoformat()}*
"""

        return template
