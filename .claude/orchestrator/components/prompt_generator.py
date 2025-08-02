#!/usr/bin/env python3
"""
PromptGenerator Component for OrchestratorAgent

Generates phase-specific prompts for WorkflowManager execution in parallel worktrees.
This component addresses the critical issue where WorkflowManagers were receiving
generic prompts instead of implementation-specific instructions.
"""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PromptContext:
    """Context information for prompt generation"""
    task_id: str
    task_name: str
    original_prompt: str
    phase_focus: Optional[str] = None
    dependencies: List[str] = None
    target_files: List[str] = None
    implementation_requirements: Dict = None


class PromptGenerator:
    """Generates phase-specific prompts for WorkflowManager execution"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.templates_dir = self.project_root / ".claude" / "orchestrator" / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize default templates if they don't exist
        self._create_default_templates()
    
    def generate_workflow_prompt(
        self,
        context: PromptContext,
        worktree_path: Path
    ) -> str:
        """Generate a complete workflow prompt for WorkflowManager execution"""
        
        prompt_content = self._build_workflow_prompt(context)
        
        # Save prompt to worktree
        prompt_file = worktree_path / "prompts" / f"{context.task_id}-workflow.md"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(prompt_file, 'w') as f:
            f.write(prompt_content)
        
        print(f"📝 Generated workflow prompt: {prompt_file}")
        return str(prompt_file)
    
    def _build_workflow_prompt(self, context: PromptContext) -> str:
        """Build the complete workflow prompt content"""
        
        # Read the original prompt to extract requirements
        original_content = self._read_original_prompt(context.original_prompt)
        
        # Extract key sections from original prompt
        sections = self._parse_prompt_sections(original_content)
        
        # Build the workflow-specific prompt
        prompt_content = f"""# WorkflowManager Task Execution

## Task Information
- **Task ID**: {context.task_id}
- **Task Name**: {context.task_name}
- **Original Prompt**: {context.original_prompt}
- **Phase Focus**: {context.phase_focus or 'Full Implementation'}

## Implementation Requirements

{sections.get('requirements', 'See original prompt for detailed requirements.')}

## Technical Specifications

{sections.get('technical_analysis', 'See original prompt for technical details.')}

## Implementation Plan

{sections.get('implementation_plan', 'Follow the implementation steps from the original prompt.')}

## Success Criteria

{sections.get('success_criteria', 'Complete all phases successfully with working implementation.')}

## Execution Instructions

**CRITICAL**: You are executing as WorkflowManager in a parallel execution environment.

1. **Complete All 9 Phases**: Execute the full WorkflowManager workflow
   - Phase 1: Initial Setup (analyze this prompt)
   - Phase 2: Issue Management (link to existing issue if provided)
   - Phase 3: Branch Management (you're already in the correct branch)
   - Phase 4: Research and Planning
   - Phase 5: **IMPLEMENTATION** (CREATE ACTUAL FILES - this is critical)
   - Phase 6: Testing
   - Phase 7: Documentation
   - Phase 8: Pull Request Creation
   - Phase 9: Code Review

2. **File Creation is Mandatory**: You MUST create actual implementation files, not just update Memory.md

3. **Context Preservation**: All implementation context is provided above

4. **Worktree Awareness**: You are executing in an isolated worktree environment

## Target Files
{self._format_target_files(context.target_files)}

## Dependencies
{self._format_dependencies(context.dependencies)}

## Original Prompt Content

```markdown
{original_content}
```

---

**Execute the complete WorkflowManager workflow for this task.**
"""
        
        return prompt_content
    
    def _read_original_prompt(self, prompt_path: str) -> str:
        """Read the original prompt file content"""
        try:
            full_path = self.project_root / prompt_path
            if not full_path.exists():
                # Try relative to prompts directory
                full_path = self.project_root / "prompts" / prompt_path
            
            if full_path.exists():
                with open(full_path, 'r') as f:
                    return f.read()
            else:
                return f"ERROR: Could not find prompt file: {prompt_path}"
                
        except Exception as e:
            return f"ERROR: Failed to read prompt file {prompt_path}: {str(e)}"
    
    def _parse_prompt_sections(self, content: str) -> Dict[str, str]:
        """Parse key sections from the prompt content"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for major section headers
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # New section
                header = line[3:].lower().strip()
                if 'requirement' in header:
                    current_section = 'requirements'
                elif 'technical' in header or 'analysis' in header:
                    current_section = 'technical_analysis'
                elif 'implementation' in header and ('plan' in header or 'step' in header):
                    current_section = 'implementation_plan'
                elif 'success' in header or 'criteria' in header:
                    current_section = 'success_criteria'
                else:
                    current_section = None
                
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # Save final section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _format_target_files(self, target_files: Optional[List[str]]) -> str:
        """Format target files section"""
        if not target_files:
            return "Target files will be determined during implementation phase."
        
        formatted = "Expected files to be created/modified:\n"
        for file_path in target_files:
            formatted += f"- `{file_path}`\n"
        
        return formatted
    
    def _format_dependencies(self, dependencies: Optional[List[str]]) -> str:
        """Format dependencies section"""
        if not dependencies:
            return "No specific dependencies identified."
        
        formatted = "Task dependencies:\n"
        for dep in dependencies:
            formatted += f"- {dep}\n"
        
        return formatted
    
    def _create_default_templates(self):
        """Create default prompt templates if they don't exist"""
        
        # Create a basic template for reference
        template_file = self.templates_dir / "workflow_template.md"
        
        if not template_file.exists():
            template_content = """# WorkflowManager Task Template

This is a template for generating WorkflowManager tasks.

## Variables Available:
- {task_id}: Unique task identifier
- {task_name}: Human-readable task name
- {original_prompt}: Path to the original prompt file
- {requirements}: Extracted requirements section
- {technical_analysis}: Extracted technical analysis
- {implementation_plan}: Extracted implementation plan
- {success_criteria}: Extracted success criteria

## Usage:
This template is used by PromptGenerator to create context-aware prompts
for WorkflowManager execution in parallel worktree environments.
"""
            
            with open(template_file, 'w') as f:
                f.write(template_content)
            
            print(f"📄 Created default template: {template_file}")
    
    def create_context_from_task(
        self,
        task: Dict,
        original_prompt_path: str,
        phase_focus: Optional[str] = None
    ) -> PromptContext:
        """Create PromptContext from task definition"""
        
        return PromptContext(
            task_id=task.get('id', 'unknown'),
            task_name=task.get('name', task.get('id', 'Unknown Task')),
            original_prompt=original_prompt_path,
            phase_focus=phase_focus,
            dependencies=task.get('dependencies', []),
            target_files=task.get('target_files', []),
            implementation_requirements=task.get('requirements', {})
        )
    
    def validate_prompt_content(self, prompt_path: str) -> List[str]:
        """Validate that a generated prompt has all required sections"""
        issues = []
        
        try:
            with open(prompt_path, 'r') as f:
                content = f.read()
            
            required_sections = [
                'Task Information',
                'Implementation Requirements', 
                'Execution Instructions',
                'Original Prompt Content'
            ]
            
            for section in required_sections:
                if section not in content:
                    issues.append(f"Missing required section: {section}")
            
            # Check for critical instructions
            if 'CREATE ACTUAL FILES' not in content:
                issues.append("Missing critical file creation instruction")
            
            if 'WorkflowManager workflow' not in content:
                issues.append("Missing WorkflowManager workflow instruction")
            
        except Exception as e:
            issues.append(f"Failed to validate prompt: {str(e)}")
        
        return issues


def main():
    """CLI entry point for PromptGenerator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate WorkflowManager prompts")
    parser.add_argument("--task-id", required=True, help="Task ID")
    parser.add_argument("--task-name", required=True, help="Task name") 
    parser.add_argument("--original-prompt", required=True, help="Original prompt file path")
    parser.add_argument("--worktree-path", required=True, help="Target worktree path")
    parser.add_argument("--phase-focus", help="Specific phase to focus on")
    parser.add_argument("--validate", action="store_true", help="Validate generated prompt")
    
    args = parser.parse_args()
    
    generator = PromptGenerator()
    
    context = PromptContext(
        task_id=args.task_id,
        task_name=args.task_name,
        original_prompt=args.original_prompt,
        phase_focus=args.phase_focus
    )
    
    try:
        # Generate prompt
        prompt_file = generator.generate_workflow_prompt(
            context,
            Path(args.worktree_path)
        )
        
        print(f"✅ Generated prompt: {prompt_file}")
        
        # Validate if requested
        if args.validate:
            issues = generator.validate_prompt_content(prompt_file)
            if issues:
                print("⚠️  Validation issues:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("✅ Prompt validation passed")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to generate prompt: {e}")
        return 1


if __name__ == "__main__":
    exit(main())