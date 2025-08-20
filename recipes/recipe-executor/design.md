# Recipe Executor Design

## Architecture Overview

The Recipe Executor follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│          CLI Interface                  │
├─────────────────────────────────────────┤
│         Orchestration Layer             │
├─────────────────────────────────────────┤
│     Recipe Parser │ Dependency Resolver │
├─────────────────────────────────────────┤
│    Code Generator │ Test Generator      │
├─────────────────────────────────────────┤
│     Validator     │ Quality Gates       │
├─────────────────────────────────────────┤
│         State Manager │ Cache           │
└─────────────────────────────────────────┘
```

## Core Components

### 1. Recipe Model (`recipe_model.py`)
```python
@dataclass
class Recipe:
    """Represents a complete recipe with all components."""
    name: str
    path: Path
    requirements: Requirements
    design: Design
    components: Components
    metadata: RecipeMetadata

@dataclass
class Requirements:
    """Parsed requirements from requirements.md."""
    purpose: str
    functional_requirements: list[Requirement]
    non_functional_requirements: list[Requirement]
    success_criteria: list[str]

@dataclass
class Design:
    """Parsed design from design.md."""
    architecture: str
    components: list[ComponentDesign]
    interfaces: list[Interface]
    implementation_notes: str

@dataclass
class Components:
    """Dependencies from components.json."""
    dependencies: list[str]
    version: str
    type: str  # "service", "agent", "library", "tool"
```

### 2. Recipe Parser (`recipe_parser.py`)
```python
class RecipeParser:
    """Parses recipe files into structured models."""
    
    def parse_recipe(self, recipe_path: Path) -> Recipe:
        """Parse a complete recipe from directory."""
        requirements = self._parse_requirements(recipe_path / "requirements.md")
        design = self._parse_design(recipe_path / "design.md")
        components = self._parse_components(recipe_path / "components.json")
        return Recipe(...)
    
    def _parse_requirements(self, path: Path) -> Requirements:
        """Parse requirements.md using markdown parser."""
        # Extract structured requirements from markdown
        pass
    
    def _parse_design(self, path: Path) -> Design:
        """Parse design.md extracting code blocks and architecture."""
        pass
    
    def _parse_components(self, path: Path) -> Components:
        """Parse components.json for dependencies."""
        pass
```

### 3. Dependency Resolver (`dependency_resolver.py`)
```python
class DependencyResolver:
    """Resolves and orders recipe dependencies."""
    
    def resolve(self, recipes: dict[str, Recipe]) -> list[Recipe]:
        """Return recipes in build order using topological sort."""
        graph = self._build_dependency_graph(recipes)
        return self._topological_sort(graph)
    
    def _build_dependency_graph(self, recipes: dict[str, Recipe]) -> Graph:
        """Build DAG from recipe dependencies."""
        pass
    
    def _detect_cycles(self, graph: Graph) -> list[list[str]]:
        """Detect circular dependencies."""
        pass
```

### 4. Code Generator (`code_generator.py`)
```python
class CodeGenerator:
    """Generates code from design specifications."""
    
    def generate(self, recipe: Recipe, context: BuildContext) -> GeneratedCode:
        """Generate code based on design and requirements."""
        template = self._select_template(recipe.design)
        code = self._generate_from_template(template, recipe)
        return self._validate_against_requirements(code, recipe.requirements)
    
    def _generate_from_template(self, template: Template, recipe: Recipe) -> str:
        """Use Jinja2 templates to generate code."""
        pass
    
    def _extract_code_from_design(self, design: Design) -> list[CodeBlock]:
        """Extract code blocks from design markdown."""
        pass
```

### 5. Test Generator (`test_generator.py`)
```python
class TestGenerator:
    """Generates tests for components."""
    
    def generate_tests(self, recipe: Recipe, code: GeneratedCode) -> TestSuite:
        """Generate comprehensive tests based on requirements."""
        unit_tests = self._generate_unit_tests(recipe, code)
        integration_tests = self._generate_integration_tests(recipe, code)
        return TestSuite(unit_tests, integration_tests)
    
    def _generate_unit_tests(self, recipe: Recipe, code: GeneratedCode) -> list[Test]:
        """Generate unit tests for each requirement."""
        pass
```

### 6. Validator (`validator.py`)
```python
class Validator:
    """Validates implementations against requirements."""
    
    def validate(self, recipe: Recipe, implementation: Implementation) -> ValidationResult:
        """Comprehensive validation of generated code."""
        results = []
        results.append(self._validate_requirements_coverage(recipe, implementation))
        results.append(self._validate_design_compliance(recipe, implementation))
        results.append(self._validate_quality_gates(implementation))
        return ValidationResult(results)
    
    def _validate_requirements_coverage(self, recipe: Recipe, impl: Implementation) -> bool:
        """Ensure all requirements are implemented."""
        pass
```

### 7. Orchestrator (`orchestrator.py`)
```python
class RecipeOrchestrator:
    """Main orchestration engine for recipe execution."""
    
    def __init__(self):
        self.parser = RecipeParser()
        self.resolver = DependencyResolver()
        self.generator = CodeGenerator()
        self.test_generator = TestGenerator()
        self.validator = Validator()
        self.state_manager = StateManager()
    
    def execute(self, recipe_path: Path, options: BuildOptions) -> BuildResult:
        """Execute a recipe and all its dependencies."""
        # 1. Parse all recipes
        recipes = self._discover_recipes(recipe_path)
        
        # 2. Resolve dependencies
        build_order = self.resolver.resolve(recipes)
        
        # 3. Execute in order
        results = []
        for recipe in build_order:
            if self.state_manager.needs_rebuild(recipe):
                result = self._execute_single(recipe, options)
                results.append(result)
                self.state_manager.record_build(recipe, result)
        
        return BuildResult(results)
    
    def _execute_single(self, recipe: Recipe, options: BuildOptions) -> SingleBuildResult:
        """Execute a single recipe."""
        # Generate code
        code = self.generator.generate(recipe)
        
        # Generate tests
        tests = self.test_generator.generate_tests(recipe, code)
        
        # Validate
        validation = self.validator.validate(recipe, Implementation(code, tests))
        
        # Run quality gates
        quality_result = self._run_quality_gates(code, tests)
        
        return SingleBuildResult(recipe, code, tests, validation, quality_result)
```

### 8. State Manager (`state_manager.py`)
```python
class StateManager:
    """Manages build state and caching."""
    
    def needs_rebuild(self, recipe: Recipe) -> bool:
        """Check if recipe needs rebuilding."""
        # Check if recipe files changed
        # Check if dependencies changed
        # Check if previous build failed
        pass
    
    def record_build(self, recipe: Recipe, result: BuildResult):
        """Record build result for caching."""
        pass
```

## Self-Hosting Implementation

The Recipe Executor achieves self-hosting through:

1. **Bootstrap Phase**: Minimal Python implementation that can read and execute its own recipe
2. **Generation Phase**: Uses bootstrap to generate full implementation from recipe
3. **Validation Phase**: Validates generated code matches current implementation
4. **Replacement Phase**: Atomically replaces implementation with generated version

```python
class SelfHostingExecutor:
    """Special executor for self-regeneration."""
    
    def regenerate(self) -> bool:
        """Regenerate Recipe Executor from its own recipe."""
        # 1. Load own recipe
        own_recipe = self.parser.parse_recipe(Path("recipes/recipe-executor"))
        
        # 2. Generate new implementation
        new_impl = self.generator.generate(own_recipe)
        
        # 3. Validate it matches current
        if not self._validate_self_consistency(new_impl):
            raise SelfHostingError("Generated code doesn't match current implementation")
        
        # 4. Run tests on new implementation
        test_result = self._test_generated_implementation(new_impl)
        
        # 5. If all passes, we've proven self-hosting works
        return test_result.passed
```

## Error Handling Strategy

1. **Parse Errors**: Clear messages about recipe file issues
2. **Dependency Errors**: Highlight circular dependencies or missing components
3. **Generation Errors**: Show which requirement couldn't be satisfied
4. **Validation Errors**: Detailed report of what doesn't match requirements
5. **Quality Gate Failures**: Specific issues from pyright, ruff, pytest

## Caching Strategy

1. **Recipe Cache**: Parsed recipes cached in memory
2. **Dependency Graph Cache**: Resolved dependencies cached per session
3. **Build Artifacts**: Generated code cached on disk with checksums
4. **Test Results**: Test outcomes cached to avoid re-running unchanged tests

## Plugin Architecture

Support for extensions through plugin interface:

```python
class RecipePlugin(ABC):
    """Base class for Recipe Executor plugins."""
    
    @abstractmethod
    def pre_generate(self, recipe: Recipe, context: BuildContext):
        """Hook before code generation."""
        pass
    
    @abstractmethod
    def post_generate(self, recipe: Recipe, code: GeneratedCode):
        """Hook after code generation."""
        pass
    
    @abstractmethod
    def custom_validator(self, recipe: Recipe, impl: Implementation) -> ValidationResult:
        """Custom validation logic."""
        pass
```

## Quality Gate Integration

Automatic execution of quality gates:
1. **pyright**: Type checking on generated code
2. **ruff format**: Code formatting
3. **ruff check**: Linting
4. **pytest**: Test execution
5. **coverage**: Test coverage analysis