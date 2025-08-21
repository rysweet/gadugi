# Recipe Executor Design

## Key Design Principles

### Separation of Concerns

1. **Recipe Dependencies (components.json)**: Lists other recipes that this recipe depends on. These are build-time dependencies for the Recipe Executor to resolve build order. Example: `{"dependencies": ["base-recipe", "utility-recipe"]}`.

2. **Python Dependencies (pyproject.toml)**: Managed by UV. Lists Python packages needed at runtime. The Recipe Executor does NOT manage pyproject.toml directly - that's handled by UV for each generated project.

3. **Generated Code Location**: Convention-based output structure. Code for recipe "foo-bar" generates to `src/foo_bar/`, tests to `tests/`, configuration to project root. No need to specify output paths in recipes.

4. **Test-Driven Development (TDD)**: Strict adherence to TDD methodology - tests are generated first, validated to fail, then implementation is generated to make them pass.

## Architecture Overview

The Recipe Executor follows a layered architecture with clear separation of concerns and support for parallel execution:

```
┌─────────────────────────────────────────────────────────┐
│              CLI Interface (cli.py)                      │
│         - Command parsing, progress display              │
├─────────────────────────────────────────────────────────┤
│         Orchestration Layer (orchestrator.py)            │
│    - Workflow coordination, parallel execution control   │
├─────────────────────────────────────────────────────────┤
│  Recipe Parser │ Dependency Resolver │ State Manager    │
│  - File parsing │ - DAG construction  │ - Build cache   │
│  - Validation   │ - Cycle detection   │ - Checksums     │
├─────────────────────────────────────────────────────────┤
│ Claude Code Gen │ Test Generator │ Python Standards     │
│ - TDD prompts   │ - pytest tests │ - UV projects       │
│ - Code parsing  │ - Fixtures     │ - pyright/ruff      │
├─────────────────────────────────────────────────────────┤
│    Validator    │ Quality Gates  │ Error Handler        │
│ - Requirements  │ - Type check   │ - Clear messages    │
│ - Coverage      │ - Format/lint  │ - Recovery logic    │
└─────────────────────────────────────────────────────────┘
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
    
    def get_dependencies(self) -> list[str]:
        """Get list of recipe dependencies."""
        return self.components.dependencies
    
    def get_checksum(self) -> str:
        """Calculate checksum of recipe files for change detection."""
        # Combines checksums of requirements.md, design.md, components.json
        pass

@dataclass
class Requirements:
    """Parsed requirements from requirements.md."""
    purpose: str
    functional_requirements: list[Requirement]
    non_functional_requirements: list[Requirement]
    success_criteria: list[str]
    
    def get_must_requirements(self) -> list[Requirement]:
        """Get only MUST priority requirements."""
        return [r for r in self.functional_requirements if r.priority == "MUST"]

@dataclass
class Requirement:
    """Single requirement with validation criteria."""
    id: str  # e.g., "req_1"
    description: str
    priority: RequirementPriority  # MUST, SHOULD, COULD
    validation_criteria: list[str]
    implemented: bool = False

@dataclass
class Design:
    """Parsed design from design.md."""
    architecture: str
    components: list[ComponentDesign]
    interfaces: list[Interface]
    implementation_notes: str
    code_blocks: list[str]  # Example code snippets

@dataclass
class ComponentDesign:
    """Design specification for a single component."""
    name: str
    description: str
    class_name: Optional[str]
    methods: list[str]
    properties: list[str]
    code_snippet: Optional[str]

@dataclass
class Components:
    """Recipe metadata from components.json."""
    name: str  # Recipe name
    version: str  # Recipe version (e.g., "1.0.0")
    type: ComponentType  # Enum: SERVICE, AGENT, LIBRARY, TOOL, CORE
    dependencies: list[str]  # Names of other recipes this depends on
    description: str
    metadata: dict[str, Any]  # Additional metadata (e.g., self_hosting: true)
```

### 2. Recipe Parser (`recipe_parser.py`)
```python
class RecipeParser:
    """Parses recipe files into structured models."""
    
    def parse_recipe(self, recipe_path: Path) -> Recipe:
        """Parse a complete recipe from directory."""
        # Validate all required files exist
        self._validate_recipe_structure(recipe_path)
        
        requirements = self._parse_requirements(recipe_path / "requirements.md")
        design = self._parse_design(recipe_path / "design.md")
        components = self._parse_components(recipe_path / "components.json")
        
        # Create metadata with checksums for change detection
        metadata = self._create_metadata(recipe_path)
        
        return Recipe(
            name=components.name,
            path=recipe_path,
            requirements=requirements,
            design=design,
            components=components,
            metadata=metadata
        )
    
    def _parse_requirements(self, path: Path) -> Requirements:
        """Parse requirements.md using markdown parser."""
        content = path.read_text()
        
        # Extract structured requirements with priorities
        functional_reqs = self._extract_requirements(content, "Functional Requirements")
        non_functional_reqs = self._extract_requirements(content, "Non-Functional Requirements")
        success_criteria = self._extract_success_criteria(content)
        
        return Requirements(
            purpose=self._extract_purpose(content),
            functional_requirements=functional_reqs,
            non_functional_requirements=non_functional_reqs,
            success_criteria=success_criteria
        )
    
    def _extract_requirements(self, content: str, section: str) -> list[Requirement]:
        """Extract requirements with MUST/SHOULD/COULD priorities."""
        # Parse markdown to find requirements like:
        # - MUST validate input files
        # - SHOULD support caching
        # - COULD provide metrics
        pass
```

### 3. Dependency Resolver (`dependency_resolver.py`)
```python
class DependencyResolver:
    """Resolves and orders recipe dependencies with parallel execution support."""
    
    def resolve(self, recipes: dict[str, Recipe]) -> list[Recipe]:
        """Return recipes in build order using topological sort."""
        graph = self._build_dependency_graph(recipes)
        
        # Check for circular dependencies
        if cycles := self._detect_cycles(graph):
            raise CircularDependencyError(
                f"Circular dependency detected: {' → '.join(cycles[0])}"
            )
        
        # Topological sort for build order
        return self._topological_sort(graph)
    
    def get_parallel_groups(self, recipes: list[Recipe]) -> list[list[Recipe]]:
        """Group recipes that can be built in parallel."""
        # Analyze dependency graph to find independent recipes
        # Return list of groups where each group can be built in parallel
        groups = []
        remaining = set(recipes)
        
        while remaining:
            # Find recipes with no dependencies in remaining set
            parallel_group = [
                r for r in remaining 
                if not any(dep in remaining for dep in r.get_dependencies())
            ]
            if not parallel_group:
                raise CircularDependencyError("Cannot determine parallel groups")
            
            groups.append(parallel_group)
            remaining -= set(parallel_group)
        
        return groups
    
    def _build_dependency_graph(self, recipes: dict[str, Recipe]) -> nx.DiGraph:
        """Build directed acyclic graph from recipe dependencies."""
        graph = nx.DiGraph()
        
        for name, recipe in recipes.items():
            graph.add_node(name, recipe=recipe)
            for dep in recipe.get_dependencies():
                if dep not in recipes:
                    raise MissingDependencyError(f"Recipe '{name}' depends on missing recipe '{dep}'")
                graph.add_edge(dep, name)  # dep must be built before name
        
        return graph
```

### 4. Claude Code Generator (`claude_code_generator.py`)
```python
class ClaudeCodeGenerator:
    """Generates code using Claude Code CLI with TDD approach."""
    
    def __init__(self, claude_command: str = "claude"):
        self.claude_command = claude_command
        self.standards = PythonStandards()
    
    def generate(self, recipe: Recipe, context: BuildContext) -> GeneratedCode:
        """Generate code using TDD methodology."""
        # Step 1: Generate comprehensive tests first (TDD Red phase)
        test_prompt = self._create_tdd_test_prompt(recipe)
        test_output = self._invoke_claude_code(test_prompt, recipe)
        test_files = self._parse_generated_files(test_output, recipe)
        
        # Step 2: Generate implementation to pass tests (TDD Green phase)
        impl_prompt = self._create_implementation_prompt(recipe, test_files)
        impl_output = self._invoke_claude_code(impl_prompt, recipe)
        impl_files = self._parse_generated_files(impl_output, recipe)
        
        # Step 3: Apply Python standards (TDD Refactor phase)
        all_files = {**test_files, **impl_files}
        for filepath, content in all_files.items():
            if filepath.endswith('.py'):
                all_files[filepath] = self.standards.format_code_with_ruff(content)
        
        # Validate generated code satisfies requirements
        generated = GeneratedCode(
            recipe_name=recipe.name,
            files=all_files,
            language="python",
            timestamp=datetime.now()
        )
        
        if not self._validate_against_requirements(generated, recipe.requirements):
            raise GenerationError("Generated code doesn't satisfy requirements")
        
        return generated
    
    def _create_tdd_test_prompt(self, recipe: Recipe) -> str:
        """Create prompt for generating tests first (TDD approach)."""
        return f"""# Generate Tests for {recipe.name}

## Test-Driven Development (TDD) Approach

You are following TDD methodology. Generate comprehensive tests FIRST that will initially FAIL.
These tests will drive the implementation.

## Requirements to Test

{self._format_requirements(recipe.requirements)}

## Success Criteria
{self._format_success_criteria(recipe.requirements.success_criteria)}

## Test Guidelines

1. Create pytest-compatible test files
2. Test ALL MUST requirements with specific test cases
3. Include unit tests for each component
4. Include integration tests for component interactions
5. Use fixtures and parameterized tests where appropriate
6. Tests should be comprehensive enough to drive implementation
7. Include edge cases and error conditions

Generate test files that will fail initially (since no implementation exists yet).
"""
    
    def _create_implementation_prompt(self, recipe: Recipe, test_files: dict[str, str]) -> str:
        """Create prompt for implementing code to pass tests."""
        return f"""# Implement Code to Pass Tests for {recipe.name}

## Your Task

Implement the code needed to make all the following tests pass.

## Existing Tests

{self._format_test_files(test_files)}

## Requirements

{self._format_requirements(recipe.requirements)}

## Design Specification

{self._format_design(recipe.design)}

## Implementation Guidelines

1. Write the minimal code needed to make tests pass
2. Follow the design specification closely
3. Use proper type hints throughout
4. Ensure all tests pass (make all tests pass)
5. No stub implementations - everything must work

Generate the implementation that makes all tests pass.
"""
    
    def _invoke_claude_code(self, prompt: str, recipe: Recipe) -> str:
        """Use Claude Code CLI to generate implementation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt_file = Path(tmpdir) / "prompt.md"
            prompt_file.write_text(prompt)
            
            cmd = [
                self.claude_command,
                "--prompt-file", str(prompt_file),
            ]
            
            result = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise ClaudeCodeGenerationError(f"Claude Code failed: {result.stderr}")
            
            return result.stdout
```

### 5. Test Generator (`test_generator.py`)
```python
class TestGenerator:
    """Generates comprehensive tests for components."""
    
    def generate_tests(self, recipe: Recipe, code: GeneratedCode) -> RecipeTestSuite:
        """Generate comprehensive tests based on requirements."""
        # Extract test targets from generated code
        test_targets = self._identify_test_targets(code)
        
        # Generate unit tests for each requirement
        unit_tests = []
        for req in recipe.requirements.get_must_requirements():
            unit_tests.extend(self._generate_requirement_tests(req, test_targets))
        
        # Generate integration tests for workflows
        integration_tests = self._generate_integration_tests(recipe, test_targets)
        
        # Generate test files with proper structure
        test_files = self._organize_test_files(unit_tests, integration_tests)
        
        return RecipeTestSuite(
            recipe_name=recipe.name,
            unit_tests=unit_tests,
            integration_tests=integration_tests,
            test_files=test_files
        )
    
    def _generate_requirement_tests(self, requirement: Requirement, targets: list) -> list[str]:
        """Generate tests for a specific requirement."""
        tests = []
        for criterion in requirement.validation_criteria:
            tests.append(self._create_test_for_criterion(criterion, targets))
        return tests
```

### 6. Validator (`validator.py`)
```python
class Validator:
    """Validates implementations against requirements."""
    
    def validate(self, recipe: Recipe, implementation: Implementation) -> ValidationResult:
        """Comprehensive validation of generated code."""
        errors = []
        warnings = []
        
        # Check requirements coverage
        req_coverage = self._validate_requirements_coverage(recipe, implementation)
        if not req_coverage.complete:
            errors.extend(req_coverage.missing)
        
        # Check design compliance
        design_compliance = self._validate_design_compliance(recipe, implementation)
        if not design_compliance.compliant:
            warnings.extend(design_compliance.issues)
        
        # Check quality gates
        quality_gates = self._validate_quality_gates(implementation)
        if not quality_gates.passed:
            errors.extend(quality_gates.failures)
        
        return ValidationResult(
            recipe_name=recipe.name,
            passed=len(errors) == 0,
            requirements_coverage=req_coverage.coverage_map,
            design_compliance=design_compliance.compliance_map,
            quality_gates=quality_gates.results,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_requirements_coverage(self, recipe: Recipe, impl: Implementation) -> CoverageResult:
        """Ensure all MUST requirements are implemented."""
        coverage_map = {}
        missing = []
        
        for req in recipe.requirements.get_must_requirements():
            # Check if requirement is satisfied in implementation
            if self._requirement_implemented(req, impl):
                coverage_map[req.id] = True
            else:
                coverage_map[req.id] = False
                missing.append(f"Requirement {req.id} not implemented: {req.description}")
        
        return CoverageResult(
            complete=len(missing) == 0,
            coverage_map=coverage_map,
            missing=missing
        )
```

### 7. Orchestrator (`orchestrator.py`)
```python
class RecipeOrchestrator:
    """Main orchestration engine for recipe execution with parallel support."""
    
    def __init__(self, recipe_root: Path = Path("recipes")):
        self.recipe_root = recipe_root
        self.parser = RecipeParser()
        self.resolver = DependencyResolver()
        self.generator = ClaudeCodeGenerator()
        self.test_generator = TestGenerator()
        self.validator = Validator()
        self.state_manager = StateManager()
        self.quality_gates = QualityGates()
    
    def execute(self, recipe_path: Path, options: BuildOptions) -> BuildResult:
        """Execute a recipe and all its dependencies."""
        # 1. Parse all recipes including dependencies
        recipes = self._discover_recipes(recipe_path)
        
        # 2. Resolve dependencies and identify parallel groups
        build_order = self.resolver.resolve(recipes)
        parallel_groups = self.resolver.get_parallel_groups(build_order)
        
        # 3. Execute in parallel groups
        results = []
        for group in parallel_groups:
            if options.parallel:
                # Execute group in parallel using ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                    futures = []
                    for recipe in group:
                        if self.state_manager.needs_rebuild(recipe, options.force_rebuild):
                            future = executor.submit(self._execute_single, recipe, options)
                            futures.append((recipe, future))
                    
                    # Collect results
                    for recipe, future in futures:
                        try:
                            result = future.result(timeout=300)
                            results.append(result)
                            self.state_manager.record_build(recipe, result)
                        except Exception as e:
                            results.append(self._create_error_result(recipe, e))
            else:
                # Execute sequentially
                for recipe in group:
                    if self.state_manager.needs_rebuild(recipe, options.force_rebuild):
                        result = self._execute_single(recipe, options)
                        results.append(result)
                        self.state_manager.record_build(recipe, result)
        
        return BuildResult(
            results=results,
            success=all(r.success for r in results),
            total_time=sum(r.build_time for r in results)
        )
    
    def _execute_single(self, recipe: Recipe, options: BuildOptions) -> SingleBuildResult:
        """Execute a single recipe following TDD approach."""
        start_time = time.time()
        errors = []
        
        try:
            # Build context with dependencies
            context = BuildContext(
                recipe=recipe,
                dependencies=self._get_built_dependencies(recipe),
                dry_run=options.dry_run,
                verbose=options.verbose
            )
            
            # Generate code using TDD (tests first, then implementation)
            code = self.generator.generate(recipe, context)
            
            # Additional test generation if needed
            tests = self.test_generator.generate_tests(recipe, code)
            
            # Create implementation object
            impl = Implementation(code=code, tests=tests)
            
            # Validate against requirements
            validation = self.validator.validate(recipe, impl)
            
            # Run quality gates if not dry run
            quality_result = {}
            if not options.dry_run:
                quality_result = self.quality_gates.run_all_gates(impl)
                if not all(quality_result.values()):
                    errors.extend([f"Quality gate failed: {k}" for k, v in quality_result.items() if not v])
            
            success = validation.passed and all(quality_result.values())
            
        except Exception as e:
            code = None
            tests = None
            validation = None
            quality_result = {}
            success = False
            errors.append(str(e))
        
        return SingleBuildResult(
            recipe=recipe,
            code=code,
            tests=tests,
            validation=validation,
            quality_result=quality_result,
            success=success,
            build_time=time.time() - start_time,
            errors=errors
        )
```

### 8. State Manager (`state_manager.py`)
```python
class StateManager:
    """Manages build state, caching, and incremental builds."""
    
    def __init__(self, cache_dir: Path = Path(".recipe-cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self._state = self._load_state()
    
    def needs_rebuild(self, recipe: Recipe, force: bool = False) -> bool:
        """Check if recipe needs rebuilding based on checksums."""
        if force:
            return True
        
        # Check if recipe has been built before
        if recipe.name not in self._state:
            return True
        
        # Check if recipe files changed (via checksum)
        current_checksum = recipe.get_checksum()
        cached_checksum = self._state[recipe.name].get("checksum")
        if current_checksum != cached_checksum:
            return True
        
        # Check if any dependencies changed
        for dep_name in recipe.get_dependencies():
            if dep_name in self._state:
                if self._state[dep_name].get("changed", False):
                    return True
        
        # Check if previous build failed
        if not self._state[recipe.name].get("success", False):
            return True
        
        return False
    
    def record_build(self, recipe: Recipe, result: SingleBuildResult):
        """Record build result for caching and incremental builds."""
        self._state[recipe.name] = {
            "checksum": recipe.get_checksum(),
            "success": result.success,
            "timestamp": datetime.now().isoformat(),
            "build_time": result.build_time,
            "changed": True  # Mark as changed for dependent recipes
        }
        
        # Save generated artifacts
        if result.code:
            self._save_artifacts(recipe, result.code)
        
        self._save_state()
    
    def _save_artifacts(self, recipe: Recipe, code: GeneratedCode):
        """Save generated code artifacts for caching."""
        artifact_dir = self.cache_dir / recipe.name
        artifact_dir.mkdir(exist_ok=True)
        
        for filepath, content in code.files.items():
            artifact_path = artifact_dir / filepath
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(content)
```

### 9. Python Standards (`python_standards.py`)
```python
class PythonStandards:
    """Enforces Python coding standards for generated code."""
    
    def __init__(self):
        self.use_uv = True
        self.use_ruff = True
        self.use_pyright = True
        self.pyright_strict = True
    
    def format_code_with_ruff(self, code: str) -> str:
        """Format Python code using ruff."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        # Run ruff format
        subprocess.run(
            ["uv", "run", "ruff", "format", temp_path],
            check=True,
            capture_output=True
        )
        
        # Read formatted code
        with open(temp_path, 'r') as f:
            formatted_code = f.read()
        
        Path(temp_path).unlink()
        return formatted_code
    
    def check_code_with_pyright(self, code: str, module_name: str = "temp") -> tuple[bool, list[str]]:
        """Check Python code with pyright for type errors."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code and pyrightconfig.json
            code_file = Path(temp_dir) / f"{module_name}.py"
            code_file.write_text(code)
            
            config_file = Path(temp_dir) / "pyrightconfig.json"
            config_file.write_text(self.get_pyrightconfig_template())
            
            # Run pyright
            result = subprocess.run(
                ["uv", "run", "pyright", str(code_file)],
                cwd=temp_dir,
                capture_output=True,
                text=True
            )
            
            # Parse errors
            errors = []
            if result.returncode != 0:
                for line in result.stdout.split('\n'):
                    if 'error:' in line:
                        errors.append(line.strip())
            
            return result.returncode == 0, errors
```

### 10. Quality Gates (`quality_gates.py`)
```python
class QualityGates:
    """Runs quality checks on generated code."""
    
    def run_all_gates(self, implementation: Implementation) -> dict[str, bool]:
        """Run all quality gates and return results."""
        results = {}
        
        # Create temporary project directory
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Write implementation files
            for filepath, content in implementation.code.files.items():
                file_path = project_dir / filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
            
            # Run quality gates
            results["pyright"] = self._run_pyright(project_dir)
            results["ruff_format"] = self._run_ruff_format(project_dir)
            results["ruff_lint"] = self._run_ruff_lint(project_dir)
            results["pytest"] = self._run_pytest(project_dir)
            results["coverage"] = self._check_coverage(project_dir)
        
        return results
    
    def _run_pyright(self, project_dir: Path) -> bool:
        """Run pyright type checking - must have zero errors."""
        result = subprocess.run(
            ["uv", "run", "pyright"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
```

## Self-Hosting Implementation

The Recipe Executor achieves self-hosting through a carefully orchestrated process:

```python
class SelfHostingExecutor:
    """Special executor for self-regeneration."""
    
    def regenerate(self) -> bool:
        """Regenerate Recipe Executor from its own recipe."""
        orchestrator = RecipeOrchestrator()
        
        # 1. Load own recipe
        own_recipe_path = Path("recipes/recipe-executor")
        own_recipe = orchestrator.parser.parse_recipe(own_recipe_path)
        
        # 2. Generate new implementation using TDD
        options = BuildOptions(dry_run=False, verbose=True)
        result = orchestrator.execute(own_recipe_path, options)
        
        # 3. Validate generated code matches current implementation
        if not self._validate_self_consistency(result):
            raise SelfHostingError("Generated code doesn't match current implementation")
        
        # 4. Run full test suite on generated implementation
        test_result = self._test_generated_implementation(result)
        if not test_result.all_passed:
            raise SelfHostingError(f"Generated implementation failed tests: {test_result.failures}")
        
        # 5. Verify the generated version can itself regenerate
        if not self._verify_recursive_generation(result):
            raise SelfHostingError("Generated version cannot regenerate itself")
        
        return True
    
    def _verify_recursive_generation(self, first_generation: BuildResult) -> bool:
        """Verify that generated code can regenerate itself."""
        # Use first generation to generate second generation
        # Compare second generation with first generation
        # They should be identical (deterministic)
        pass
```

## Error Handling Strategy

Clear, actionable error messages at each level:

```python
class ErrorHandler:
    """Provides clear, actionable error messages."""
    
    def format_parse_error(self, file: Path, line: int, issue: str) -> str:
        """Format recipe parsing errors."""
        return f"""
Error parsing recipe file: {file}
Line {line}: {issue}

Example of correct format:
- MUST implement user authentication
  - Validation: All endpoints require valid JWT token
  - Validation: Tokens expire after 1 hour

Please fix the recipe file and try again.
"""
    
    def format_dependency_error(self, recipe: str, missing: list[str]) -> str:
        """Format missing dependency errors."""
        return f"""
Recipe '{recipe}' has missing dependencies:
{chr(10).join(f'  - {dep}' for dep in missing)}

To fix this:
1. Ensure the dependency recipes exist in the recipes/ directory
2. Check the spelling of dependency names in components.json
3. Run with --verbose to see the dependency resolution process
"""
    
    def format_circular_dependency(self, cycle: list[str]) -> str:
        """Format circular dependency errors."""
        return f"""
Circular dependency detected:
{' → '.join(cycle)} → {cycle[0]}

This creates an infinite loop that cannot be resolved.

To fix this:
1. Review the dependencies in each recipe's components.json
2. Extract common functionality to a shared base recipe
3. Consider if the dependency is truly needed
"""
```

## Parallel Execution Strategy

Maximize CPU utilization through intelligent parallelization:

```python
class ParallelExecutor:
    """Manages parallel execution of independent recipes."""
    
    def execute_parallel_group(self, recipes: list[Recipe], options: BuildOptions) -> list[BuildResult]:
        """Execute a group of independent recipes in parallel."""
        max_workers = min(len(recipes), os.cpu_count() or 4)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all recipes for parallel execution
            futures = {
                executor.submit(self._execute_recipe, recipe, options): recipe
                for recipe in recipes
            }
            
            # Collect results with progress tracking
            results = []
            with tqdm(total=len(recipes)) as pbar:
                for future in concurrent.futures.as_completed(futures):
                    recipe = futures[future]
                    try:
                        result = future.result(timeout=300)
                        results.append(result)
                        pbar.update(1)
                        pbar.set_description(f"Completed: {recipe.name}")
                    except Exception as e:
                        results.append(self._create_error_result(recipe, e))
                        pbar.update(1)
                        pbar.set_description(f"Failed: {recipe.name}")
            
            return results
```

## Incremental Build Optimization

Efficient change detection and targeted rebuilds:

```python
class IncrementalBuilder:
    """Optimizes builds by detecting and rebuilding only changed components."""
    
    def analyze_changes(self, recipes: dict[str, Recipe]) -> ChangeSet:
        """Analyze which recipes have changed and need rebuilding."""
        changed = set()
        affected = set()
        
        for name, recipe in recipes.items():
            # Check if recipe files changed
            if self._has_recipe_changed(recipe):
                changed.add(name)
                # Mark all dependents as affected
                affected.update(self._get_all_dependents(name, recipes))
        
        return ChangeSet(
            directly_changed=changed,
            affected_by_dependencies=affected,
            total_to_rebuild=changed | affected,
            unchanged=set(recipes.keys()) - (changed | affected)
        )
    
    def _has_recipe_changed(self, recipe: Recipe) -> bool:
        """Check if recipe has changed since last build."""
        current_checksum = self._calculate_checksum(recipe)
        cached_checksum = self.cache.get_checksum(recipe.name)
        return current_checksum != cached_checksum
```

## Progress Tracking and Reporting

Real-time feedback during execution:

```python
class ProgressTracker:
    """Provides clear progress indicators during execution."""
    
    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
    
    def track_execution(self, recipes: list[Recipe]) -> ProgressContext:
        """Track execution progress with detailed status."""
        with self.progress:
            task = self.progress.add_task(
                f"Building {len(recipes)} recipes",
                total=len(recipes)
            )
            
            for recipe in recipes:
                self.progress.update(
                    task,
                    description=f"Building {recipe.name}...",
                    advance=0
                )
                
                yield recipe
                
                self.progress.update(task, advance=1)
```

## Plugin Architecture

Support for extensions through a well-defined plugin interface:

```python
class RecipePlugin(ABC):
    """Base class for Recipe Executor plugins."""
    
    @abstractmethod
    def pre_parse(self, recipe_path: Path) -> None:
        """Hook before recipe parsing."""
        pass
    
    @abstractmethod
    def post_parse(self, recipe: Recipe) -> Recipe:
        """Hook after recipe parsing, can modify recipe."""
        pass
    
    @abstractmethod
    def pre_generate(self, recipe: Recipe, context: BuildContext) -> BuildContext:
        """Hook before code generation, can modify context."""
        pass
    
    @abstractmethod
    def post_generate(self, recipe: Recipe, code: GeneratedCode) -> GeneratedCode:
        """Hook after code generation, can modify generated code."""
        pass
    
    @abstractmethod
    def custom_validator(self, recipe: Recipe, impl: Implementation) -> ValidationResult:
        """Custom validation logic."""
        pass
    
    @abstractmethod
    def custom_quality_gate(self, impl: Implementation) -> tuple[str, bool]:
        """Custom quality gate check."""
        pass

class PluginManager:
    """Manages Recipe Executor plugins."""
    
    def __init__(self):
        self.plugins: list[RecipePlugin] = []
    
    def load_plugins(self, plugin_dir: Path = Path("plugins")):
        """Dynamically load plugins from directory."""
        for plugin_file in plugin_dir.glob("*.py"):
            module = importlib.import_module(plugin_file.stem)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, RecipePlugin):
                    self.plugins.append(obj())
    
    def execute_hook(self, hook_name: str, *args, **kwargs):
        """Execute a hook on all plugins."""
        results = []
        for plugin in self.plugins:
            if hasattr(plugin, hook_name):
                result = getattr(plugin, hook_name)(*args, **kwargs)
                results.append(result)
        return results
```