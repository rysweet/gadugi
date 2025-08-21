# Recipe Executor - Complete Design Architecture

## Overview

Recipe Executor is a self-hosting build system that transforms recipe specifications into fully functional software components using AI-powered code generation (specifically Claude CLI).

## Key Design Decisions

### 1. AI Implementation Choice: Claude CLI
- **Technology**: Claude Code CLI (`claude -p`) for all code generation
- **Rationale**: Built-in retry logic, consistent quality, no need for templates
- **Note**: Claude CLI handles its own exponential backoff and retry logic

### 2. TDD-First Approach
- Tests generated before implementation
- Red-Green-Refactor cycle with iterative fixing
- TestSolver agent fixes failing tests until all pass

### 3. Multi-Stage Validation
- Pre-execution: Recipe structure and separation validation
- During execution: Code review iterations
- Post-execution: Requirements compliance validation

## Complete Execution Pipeline

### Stage 1: Recipe Validation & Preparation

```python
class RecipeValidator:
    """Validates recipe structure and separation of concerns."""
    
    def validate_separation(self, recipe: Recipe) -> ValidationResult:
        """Check requirements vs design separation."""
        issues = []
        
        # Check requirements.md for HOW details
        req_text = recipe.requirements_path.read_text()
        how_patterns = [
            r'MUST use (PostgreSQL|MySQL|Redis)',  # Technology choice
            r'MUST implement using',                 # Implementation detail
            r'MUST call.*API',                      # Specific integration
        ]
        for pattern in how_patterns:
            if re.search(pattern, req_text):
                issues.append(f"Requirements contain HOW: {pattern}")
        
        # Check design.md for WHAT details  
        design_text = recipe.design_path.read_text()
        what_patterns = [
            r'MUST \w+',                           # Requirements language
            r'system shall',                       # Functional requirement
            r'business rule',                      # Business logic
        ]
        for pattern in what_patterns:
            if re.search(pattern, design_text):
                issues.append(f"Design contains WHAT: {pattern}")
        
        if issues:
            # Use Claude to propose corrections
            corrected = self._propose_corrections(recipe, issues)
            return ValidationResult(valid=False, issues=issues, corrections=corrected)
        
        return ValidationResult(valid=True)
    
    def _propose_corrections(self, recipe: Recipe, issues: List[str]) -> Dict[str, str]:
        """Use Claude to generate properly separated requirements and design."""
        prompt = f"""
        The following recipe has mixed requirements (WHAT) and design (HOW):
        
        Issues found:
        {chr(10).join(issues)}
        
        Current requirements:
        {recipe.requirements_path.read_text()}
        
        Current design:
        {recipe.design_path.read_text()}
        
        Please provide corrected versions that properly separate:
        - Requirements: Only WHAT the system must do (behavior, capabilities)
        - Design: Only HOW to implement it (technologies, algorithms, architecture)
        """
        
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        return self._parse_corrections(result.stdout)
```

### Stage 2: Recipe Complexity Evaluation

```python
class RecipeDecomposer:
    """Evaluates and decomposes complex recipes."""
    
    COMPLEXITY_THRESHOLDS = {
        'max_components': 10,
        'max_requirements': 20,
        'max_functional_areas': 3
    }
    
    def evaluate_complexity(self, recipe: Recipe) -> ComplexityResult:
        """Determine if recipe needs decomposition."""
        score = 0
        reasons = []
        
        # Check component count
        component_count = len(recipe.design.components)
        if component_count > self.COMPLEXITY_THRESHOLDS['max_components']:
            score += 3
            reasons.append(f"{component_count} components exceeds threshold")
        
        # Check requirement count
        req_count = len(recipe.requirements.get_all_requirements())
        if req_count > self.COMPLEXITY_THRESHOLDS['max_requirements']:
            score += 3
            reasons.append(f"{req_count} requirements exceeds threshold")
        
        # Check for mixed concerns
        functional_areas = self._identify_functional_areas(recipe)
        if len(functional_areas) > self.COMPLEXITY_THRESHOLDS['max_functional_areas']:
            score += 4
            reasons.append(f"Mixing {len(functional_areas)} functional areas")
        
        return ComplexityResult(
            score=score,
            needs_decomposition=score >= 5,
            reasons=reasons,
            suggested_decomposition=self._suggest_decomposition(recipe, functional_areas)
        )
    
    def decompose_recipe(self, recipe: Recipe, strategy: str) -> List[Recipe]:
        """Split recipe into sub-recipes."""
        if strategy == "functional":
            return self._functional_decomposition(recipe)
        elif strategy == "layered":
            return self._layer_decomposition(recipe)
        else:
            return self._risk_based_decomposition(recipe)
```

### Stage 3: TDD Test Generation (RED Phase)

```python
class TestGenerator:
    """Generates comprehensive test suites following TDD."""
    
    def generate_tests(self, recipe: Recipe) -> TestFiles:
        """Generate tests that should initially fail."""
        prompt = f"""
        Generate comprehensive pytest tests for the following requirements.
        These tests should:
        1. Cover ALL MUST requirements
        2. Include edge cases and error conditions
        3. Use proper fixtures and parameterization
        4. Be designed to FAIL initially (no implementation exists yet)
        
        Requirements:
        {self._format_requirements(recipe.requirements)}
        
        Design components to test:
        {self._format_components(recipe.design.components)}
        
        Generate tests that will drive the implementation.
        """
        
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        test_files = self._parse_test_files(result.stdout)
        
        # Verify tests would fail
        if not self._verify_tests_fail(test_files):
            raise ValueError("Tests must fail initially (RED phase)")
        
        return test_files
```

### Stage 4: Implementation Generation (GREEN Phase)

```python
class ImplementationGenerator:
    """Generates implementation to pass tests."""
    
    def generate_implementation(self, recipe: Recipe, test_files: TestFiles) -> CodeFiles:
        """Generate code to make tests pass."""
        prompt = f"""
        Implement code to make the following tests pass.
        
        Tests to satisfy:
        {self._format_test_files(test_files)}
        
        Requirements:
        {self._format_requirements(recipe.requirements)}
        
        Design specification:
        {self._format_design(recipe.design)}
        
        Generate minimal implementation that makes all tests pass.
        Follow the design architecture and use specified technologies.
        """
        
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        return self._parse_code_files(result.stdout)
```

### Stage 5: Test Fixing Iterations

```python
class TestSolver:
    """Iteratively fixes failing tests."""
    
    MAX_ITERATIONS = 5
    
    def fix_failing_tests(self, code: CodeFiles, tests: TestFiles) -> FixResult:
        """Run tests and fix failures iteratively."""
        for iteration in range(self.MAX_ITERATIONS):
            # Run tests
            test_result = self._run_tests(tests)
            
            if test_result.all_passed:
                return FixResult(success=True, iterations=iteration)
            
            # Analyze failures
            analysis = self._analyze_failures(test_result)
            
            # Generate fixes
            fixes = self._generate_fixes(code, tests, analysis)
            
            # Apply fixes
            code = self._apply_fixes(code, fixes)
        
        return FixResult(success=False, iterations=self.MAX_ITERATIONS)
    
    def _generate_fixes(self, code: CodeFiles, tests: TestFiles, 
                       analysis: FailureAnalysis) -> Fixes:
        """Use Claude to generate fixes for failures."""
        prompt = f"""
        The following tests are failing:
        
        Failures:
        {self._format_failures(analysis)}
        
        Current implementation:
        {self._format_code(code)}
        
        Tests:
        {self._format_tests(tests)}
        
        Generate fixes to make the failing tests pass.
        Do not change test expectations unless they are incorrect.
        """
        
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        return self._parse_fixes(result.stdout)
```

### Stage 6: Code Review Cycle

```python
class CodeReviewer:
    """Reviews generated code for quality and compliance."""
    
    def review_code(self, code: CodeFiles, recipe: Recipe) -> ReviewResult:
        """Perform comprehensive code review."""
        prompt = f"""
        Review the following code for:
        1. Zero BS principle (no stubs, no placeholders)
        2. Simplicity (no over-engineering)
        3. Security vulnerabilities
        4. Code quality and maintainability
        5. Adherence to requirements
        
        Code to review:
        {self._format_code(code)}
        
        Requirements it should satisfy:
        {self._format_requirements(recipe.requirements)}
        
        Categorize issues as:
        - CRITICAL: Must fix before proceeding
        - SUGGESTION: Nice to have improvements
        
        Provide specific line-by-line feedback.
        """
        
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        return self._parse_review_feedback(result.stdout)

class CodeReviewResponse:
    """Addresses code review feedback."""
    
    def address_feedback(self, code: CodeFiles, review: ReviewResult) -> CodeFiles:
        """Fix critical issues from review."""
        if not review.has_critical_issues:
            return code
        
        prompt = f"""
        Fix the following critical issues in the code:
        
        Critical issues:
        {self._format_critical_issues(review.critical_issues)}
        
        Current code:
        {self._format_code(code)}
        
        Generate corrected code that addresses all critical issues.
        Document why suggestions were not implemented if applicable.
        """
        
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        return self._parse_corrected_code(result.stdout)
```

### Stage 7: Post-Generation Validation

```python
class RequirementsValidator:
    """Validates that generated artifacts meet requirements."""
    
    def validate_compliance(self, artifacts: Artifacts, recipe: Recipe) -> ComplianceResult:
        """Check all requirements are satisfied."""
        prompt = f"""
        Validate that the following artifacts satisfy all requirements:
        
        Requirements:
        {self._format_requirements(recipe.requirements)}
        
        Generated artifacts:
        {self._format_artifacts(artifacts)}
        
        For each MUST requirement, identify:
        1. Where it is implemented (file and line numbers)
        2. How it is tested
        3. Whether it fully satisfies the requirement
        
        Generate a compliance matrix showing requirement-to-code mapping.
        Flag any unsatisfied requirements.
        """
        
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        compliance = self._parse_compliance_matrix(result.stdout)
        
        if not compliance.all_must_satisfied:
            raise ComplianceError(f"Unsatisfied requirements: {compliance.unsatisfied}")
        
        return compliance
```

## Orchestration Flow

```python
class RecipeOrchestrator:
    """Main orchestration engine with all stages."""
    
    def execute(self, recipe_path: Path, options: BuildOptions) -> BuildResult:
        """Execute complete recipe with all validation stages."""
        
        # Stage 1: Validate recipe structure and separation
        recipe = self.parser.parse_recipe(recipe_path)
        validation = self.validator.validate_separation(recipe)
        if not validation.valid:
            if options.auto_fix_separation:
                recipe = self.apply_corrections(recipe, validation.corrections)
            else:
                return BuildResult(success=False, errors=validation.issues)
        
        # Stage 2: Evaluate complexity
        complexity = self.decomposer.evaluate_complexity(recipe)
        if complexity.needs_decomposition:
            sub_recipes = self.decomposer.decompose_recipe(
                recipe, 
                complexity.suggested_strategy
            )
            # Recursively execute sub-recipes
            return self.execute_sub_recipes(sub_recipes, options)
        
        # Stage 3: Generate tests (RED phase)
        tests = self.test_generator.generate_tests(recipe)
        
        # Stage 4: Generate implementation (GREEN phase)
        code = self.implementation_generator.generate_implementation(recipe, tests)
        
        # Stage 5: Fix failing tests iteratively
        fix_result = self.test_solver.fix_failing_tests(code, tests)
        if not fix_result.success:
            return BuildResult(success=False, errors=["Could not fix all tests"])
        
        # Stage 6: Code review cycle
        review = self.code_reviewer.review_code(code, recipe)
        while review.has_critical_issues:
            code = self.review_response.address_feedback(code, review)
            review = self.code_reviewer.review_code(code, recipe)
        
        # Stage 7: Quality gates
        quality_result = self.quality_gates.run_all_gates(code)
        if not quality_result.all_passed:
            return BuildResult(success=False, errors=quality_result.failures)
        
        # Stage 8: Post-generation validation
        artifacts = self.create_artifacts(code, tests)
        compliance = self.requirements_validator.validate_compliance(artifacts, recipe)
        
        return BuildResult(
            success=True,
            artifacts=artifacts,
            compliance=compliance
        )
```

## Design Patterns

### Separation of Concerns Pattern
- Parser: Only parses files
- Validator: Only validates structure
- Generator: Only generates code
- Reviewer: Only reviews quality
- Each component has single responsibility

### Pipeline Pattern
- Each stage has clear input/output
- Stages can be tested independently
- Failed stages can be retried
- Progress is trackable

### Agent Delegation Pattern
- Complex tasks delegated to specialized agents
- Each agent has specific tools and capabilities
- Agents communicate through structured interfaces

## Error Handling Strategy

All errors are explicit and actionable:
- Missing files: List exact files needed
- Mixed concerns: Show specific violations
- Failed tests: Provide detailed failure analysis
- Review issues: Line-by-line feedback
- Compliance failures: Exact requirement not met

## Technology Stack

- **AI Generation**: Claude CLI (built-in retry logic)
- **Testing**: pytest with fixtures and parameterization
- **Type Checking**: pyright in strict mode
- **Formatting**: ruff
- **Package Management**: UV
- **Process Execution**: subprocess with proper error handling
- **Parallel Execution**: ThreadPoolExecutor for independent recipes