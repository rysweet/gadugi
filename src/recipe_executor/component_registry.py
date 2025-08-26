"""Component Registry for Recipe Executor - ensures all required components are generated."""

from typing import Dict, List, Tuple, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """Registry of all required components for Recipe Executor self-hosting."""
    
    # Core components required for bootstrap
    BOOTSTRAP_COMPONENTS = {
        'stub_detector': 'src/stub_detector.py',
        'intelligent_stub_detector': 'src/intelligent_stub_detector.py', 
        'base_generator': 'src/base_generator.py',
    }
    
    # All required components for complete system
    REQUIRED_COMPONENTS = {
        # Data Models
        'recipe_model': 'src/recipe_model.py',
        
        # Parsing & Validation
        'recipe_parser': 'src/recipe_parser.py',
        'recipe_validator': 'src/recipe_validator.py',
        'recipe_decomposer': 'src/recipe_decomposer.py',
        'dependency_resolver': 'src/dependency_resolver.py',
        
        # Generation
        'claude_code_generator': 'src/claude_code_generator.py',
        'test_generator': 'src/test_generator.py',
        'test_solver': 'src/test_solver.py',
        'base_generator': 'src/base_generator.py',
        
        # Quality & Review
        'code_reviewer': 'src/code_reviewer.py',
        'code_review_response': 'src/code_review_response.py',
        'requirements_validator': 'src/requirements_validator.py',
        'validator': 'src/validator.py',
        'quality_gates': 'src/quality_gates.py',
        
        # Stub Detection
        'stub_detector': 'src/stub_detector.py',
        'intelligent_stub_detector': 'src/intelligent_stub_detector.py',
        
        # Orchestration
        'orchestrator': 'src/orchestrator.py',
        'state_manager': 'src/state_manager.py',
        'parallel_builder': 'src/parallel_builder.py',
        
        # Standards & Utilities
        'python_standards': 'src/python_standards.py',
        'pattern_manager': 'src/pattern_manager.py',
        'prompt_loader': 'src/prompt_loader.py',
        'language_detector': 'src/language_detector.py',
        'uv_environment': 'src/uv_environment.py',
        
        # Entry Points
        '__init__': 'src/__init__.py',
        '__main__': 'src/__main__.py',
        'cli': 'cli.py',
        
        # Configuration
        'pyproject.toml': 'pyproject.toml',
        'README.md': 'README.md',
        
        # Tests
        'test_init': 'tests/__init__.py',
        'test_recipe_executor': 'tests/test_recipe_executor.py',
    }
    
    # Generation phases for parallel execution
    GENERATION_PHASES = {
        'phase1_bootstrap': [
            'stub_detector',
            'intelligent_stub_detector', 
            'base_generator',
        ],
        'phase2_models': [
            'recipe_model',
            'code_review_response',
        ],
        'phase3_parsing': [
            'recipe_parser',
            'recipe_validator',
            'recipe_decomposer',
            'dependency_resolver',
        ],
        'phase4_generation': [
            'claude_code_generator',
            'test_generator',
            'test_solver',
        ],
        'phase5_quality': [
            'code_reviewer',
            'requirements_validator',
            'validator',
            'quality_gates',
        ],
        'phase6_orchestration': [
            'orchestrator',
            'state_manager',
            'parallel_builder',
        ],
        'phase7_utilities': [
            'python_standards',
            'pattern_manager',
            'prompt_loader',
            'language_detector',
            'uv_environment',
        ],
        'phase8_entry': [
            '__init__',
            '__main__',
            'cli',
        ],
        'phase9_config': [
            'pyproject.toml',
            'README.md',
        ],
        'phase10_tests': [
            'test_init',
            'test_recipe_executor',
        ],
    }
    
    def __init__(self):
        """Initialize the component registry."""
        self.generated_components: Set[str] = set()
        
    def validate_completeness(self, generated_files: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate that all required components have been generated.
        
        Args:
            generated_files: Dictionary mapping file paths to content
            
        Returns:
            Tuple of (is_complete, list_of_missing_components)
        """
        missing = []
        
        # Normalize paths for comparison
        normalized_generated = set()
        for filepath in generated_files.keys():
            # Remove any leading directory parts before src/ or tests/
            path = Path(filepath)
            if 'src' in path.parts:
                idx = path.parts.index('src')
                normalized = '/'.join(path.parts[idx:])
                normalized_generated.add(normalized)
            elif 'tests' in path.parts:
                idx = path.parts.index('tests')
                normalized = '/'.join(path.parts[idx:])
                normalized_generated.add(normalized)
            elif path.name in ['cli.py', 'pyproject.toml', 'README.md']:
                normalized_generated.add(path.name)
                
        # Check each required component
        for component_name, expected_path in self.REQUIRED_COMPONENTS.items():
            if expected_path not in normalized_generated:
                missing.append(f"{component_name} ({expected_path})")
                logger.warning(f"Missing component: {component_name} at {expected_path}")
            else:
                self.generated_components.add(component_name)
                
        is_complete = len(missing) == 0
        
        if is_complete:
            logger.info(f"✅ All {len(self.REQUIRED_COMPONENTS)} required components generated")
        else:
            logger.warning(f"❌ Missing {len(missing)} components: {missing[:5]}...")
            
        return is_complete, missing
    
    def get_generation_phases(self) -> Dict[str, List[str]]:
        """
        Get the phased generation plan for parallel execution.
        
        Returns:
            Dictionary mapping phase names to component lists
        """
        return self.GENERATION_PHASES
    
    def get_bootstrap_components(self) -> Dict[str, str]:
        """
        Get the minimal bootstrap components needed to start generation.
        
        Returns:
            Dictionary mapping component names to paths
        """
        return self.BOOTSTRAP_COMPONENTS
    
    def get_missing_components(self, generated_files: Dict[str, str]) -> List[str]:
        """
        Get list of components that still need to be generated.
        
        Args:
            generated_files: Current generated files
            
        Returns:
            List of component names that are missing
        """
        _, missing = self.validate_completeness(generated_files)
        return missing
    
    def create_component_checklist(self) -> str:
        """
        Create a markdown checklist of all required components.
        
        Returns:
            Markdown formatted checklist
        """
        checklist = ["# Recipe Executor Component Checklist\n\n"]
        
        for phase_name, components in self.GENERATION_PHASES.items():
            phase_num = phase_name.split('_')[0].replace('phase', 'Phase ')
            phase_desc = phase_name.split('_')[1].title()
            checklist.append(f"## {phase_num}: {phase_desc}\n\n")
            
            for component in components:
                if component in self.generated_components:
                    checklist.append(f"- [x] {component}\n")
                else:
                    checklist.append(f"- [ ] {component}\n")
            checklist.append("\n")
            
        return ''.join(checklist)
    
    def get_component_prompt_list(self) -> str:
        """
        Get a formatted list of all components for inclusion in prompts.
        
        Returns:
            Formatted string listing all required components
        """
        lines = ["**REQUIRED COMPONENTS - ALL MUST BE GENERATED:**\n\n"]
        
        for phase_name, components in self.GENERATION_PHASES.items():
            phase_desc = phase_name.split('_')[1].title()
            lines.append(f"### {phase_desc} Components\n")
            
            for component in components:
                path = self.REQUIRED_COMPONENTS.get(component, '')
                lines.append(f"- `{path}` - {component}\n")
            lines.append("\n")
            
        return ''.join(lines)