"""Prompt loader for Recipe Executor - loads and assembles prompts with context."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptLoader:
    """Loads and assembles prompts from templates and context files."""

    def __init__(self, prompts_dir: Optional[Path] = None, context_dir: Optional[Path] = None):
        """Initialize prompt loader with directories.

        Args:
            prompts_dir: Directory containing prompt templates
            context_dir: Directory containing always-included context
        """
        base_dir = Path(__file__).parent
        self.prompts_dir = prompts_dir or base_dir / "prompts"
        self.context_dir = context_dir or base_dir / "context"

        # Ensure directories exist
        if not self.prompts_dir.exists():
            raise ValueError(f"Prompts directory not found: {self.prompts_dir}")
        if not self.context_dir.exists():
            raise ValueError(f"Context directory not found: {self.context_dir}")

    def load_prompt_template(self, template_name: str) -> str:
        """Load a prompt template by name.

        Args:
            template_name: Name of template file (without .md extension)

        Returns:
            Template content
        """
        template_path = self.prompts_dir / f"{template_name}.md"
        if not template_path.exists():
            raise ValueError(f"Prompt template not found: {template_path}")

        return template_path.read_text()

    def load_context_files(self) -> Dict[str, str]:
        """Load all context files that should be included in every prompt.

        Returns:
            Dictionary mapping filename to content
        """
        context = {}

        # Load all .md files from context directory
        for context_file in self.context_dir.glob("*.md"):
            try:
                context[context_file.name] = context_file.read_text()
                logger.debug(f"Loaded context file: {context_file.name}")
            except Exception as e:
                logger.warning(f"Could not load context file {context_file}: {e}")

        return context

    def assemble_prompt(
        self, template_name: str, variables: Dict[str, str], include_context: bool = True
    ) -> str:
        """Assemble a complete prompt from template and context.

        Args:
            template_name: Name of prompt template to use
            variables: Variables to substitute in template
            include_context: Whether to include context files

        Returns:
            Complete assembled prompt
        """
        # Load template
        template = self.load_prompt_template(template_name)

        # Substitute variables in template
        prompt = template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        # Add context if requested
        if include_context:
            context_files = self.load_context_files()
            if context_files:
                # Prepend critical context to the prompt
                context_sections = []

                # Always include CRITICAL_GUIDELINES first if it exists
                if "CRITICAL_GUIDELINES.md" in context_files:
                    context_sections.append(context_files["CRITICAL_GUIDELINES.md"])
                    context_sections.append("")  # Empty line separator

                # Include Guidelines.md if it exists
                if "Guidelines.md" in context_files:
                    context_sections.append("## Project Development Guidelines")
                    context_sections.append("")
                    context_sections.append(context_files["Guidelines.md"])
                    context_sections.append("")

                # Include any other context files
                for name, content in context_files.items():
                    if name not in ["CRITICAL_GUIDELINES.md", "Guidelines.md"]:
                        context_sections.append(f"## Additional Context: {name}")
                        context_sections.append("")
                        context_sections.append(content)
                        context_sections.append("")

                # Prepend all context to the prompt
                if context_sections:
                    prompt = "\n".join(context_sections) + "\n---\n\n" + prompt

        return prompt

    def get_available_templates(self) -> List[str]:
        """Get list of available prompt templates.

        Returns:
            List of template names (without .md extension)
        """
        templates = []
        for template_file in self.prompts_dir.glob("*.md"):
            templates.append(template_file.stem)
        return sorted(templates)

    def get_context_files(self) -> List[str]:
        """Get list of context files that will be included.

        Returns:
            List of context file names
        """
        files = []
        for context_file in self.context_dir.glob("*.md"):
            files.append(context_file.name)
        return sorted(files)
