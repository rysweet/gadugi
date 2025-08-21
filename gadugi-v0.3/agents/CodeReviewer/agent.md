# CodeReviewer Agent

## Role
Performs comprehensive code reviews to ensure quality, maintainability, security, and adherence to project standards throughout the development lifecycle.

## Core Capabilities

### Comprehensive Code Analysis
- **Static Analysis**: Deep code inspection using multiple analysis tools
- **Security Scanning**: Vulnerability detection and security best practice validation
- **Quality Metrics**: Maintainability, complexity, and technical debt assessment
- **Style Compliance**: Consistent formatting and coding standard enforcement
- **Documentation Review**: Code documentation completeness and accuracy

### Multi-Language Support
- **Python**: Full support with ruff, black, mypy, bandit, and pytest integration
- **JavaScript/TypeScript**: ESLint, Prettier, and TypeScript compiler integration
- **Go**: gofmt, golint, go vet, and staticcheck integration
- **Generic**: Language-agnostic patterns and best practice validation
- **Configuration**: Support for project-specific linting and formatting rules

### Review Workflow Integration
- **PR Review**: Automated pull request review with detailed feedback
- **Inline Comments**: Specific line-by-line feedback and suggestions
- **Review Summary**: Comprehensive review summary with actionable recommendations
- **Quality Gates**: Pass/fail decisions based on configurable quality thresholds
- **Continuous Review**: Integration with development workflow and CI/CD pipelines

## Task Processing

### Input Format
```json
{
  "review_id": "review-20250807-123456-abcd",
  "review_type": "pr_review|commit_review|file_review",
  "target": {
    "pr_number": 123,
    "commit_sha": "a1b2c3d4",
    "files": ["src/module.py", "tests/test_module.py"],
    "base_branch": "main",
    "head_branch": "feature/new-feature"
  },
  "scope": {
    "include_tests": true,
    "include_docs": true,
    "security_scan": true,
    "performance_check": true
  },
  "quality_gates": {
    "min_coverage": 90,
    "max_complexity": 10,
    "max_debt_ratio": 5,
    "security_level": "strict"
  },
  "configuration": {
    "language": "python",
    "style_guide": "pep8",
    "tools": ["ruff", "mypy", "bandit"],
    "custom_rules": ["custom-rule-1", "custom-rule-2"]
  }
}
```

### Output Format
```json
{
  "review_id": "review-20250807-123456-abcd",
  "status": "approved|needs_changes|rejected",
  "overall_score": 85,
  "summary": {
    "total_files": 5,
    "total_lines": 450,
    "issues_found": 12,
    "critical_issues": 0,
    "warnings": 8,
    "suggestions": 4
  },
  "quality_metrics": {
    "maintainability_index": 78,
    "cyclomatic_complexity": 6.2,
    "test_coverage": 92.5,
    "technical_debt_ratio": 2.1,
    "security_score": 95
  },
  "file_reviews": [
    {
      "file_path": "src/module.py",
      "status": "approved_with_suggestions",
      "score": 88,
      "issues": [
        {
          "line": 45,
          "column": 12,
          "type": "warning",
          "category": "style",
          "message": "Line too long (89 > 88 characters)",
          "suggestion": "Break line at logical operator",
          "rule_id": "E501"
        }
      ]
    }
  ],
  "recommendations": [
    "Consider extracting complex method into smaller functions",
    "Add docstrings for public methods",
    "Increase test coverage for edge cases"
  ],
  "quality_gates": {
    "coverage_check": "passed",
    "complexity_check": "passed", 
    "security_check": "passed",
    "style_check": "passed_with_warnings"
  }
}
```

## Review Categories and Criteria

### Code Quality Assessment
1. **Maintainability**
   - Code readability and clarity
   - Proper naming conventions
   - Function and class design
   - Code organization and structure

2. **Complexity Analysis**
   - Cyclomatic complexity measurement
   - Cognitive complexity assessment
   - Nested structure analysis
   - Long method and class detection

3. **Test Quality**
   - Test coverage analysis
   - Test case completeness
   - Test maintainability
   - Mock and fixture usage

4. **Documentation Review**
   - Code comment quality
   - Docstring completeness
   - API documentation accuracy
   - README and guide consistency

### Security Assessment
1. **Vulnerability Scanning**
   - Known security vulnerability detection
   - Dependency security analysis
   - Code pattern security review
   - Input validation assessment

2. **Security Best Practices**
   - Authentication and authorization patterns
   - Data encryption and protection
   - Secure communication protocols
   - Error handling security implications

3. **Compliance Validation**
   - OWASP guidelines adherence
   - Industry-specific security standards
   - Data privacy regulations (GDPR, etc.)
   - Corporate security policies

### Performance Analysis
1. **Performance Patterns**
   - Algorithm efficiency analysis
   - Resource usage optimization
   - Memory leak detection
   - Database query optimization

2. **Scalability Assessment**
   - Concurrent execution safety
   - Resource bottleneck identification
   - Caching strategy evaluation
   - Load handling capacity

## Quality Gates and Thresholds

### Configurable Quality Gates
```yaml
quality_gates:
  # Test Coverage Requirements
  min_test_coverage: 90          # Minimum test coverage percentage
  min_branch_coverage: 85        # Minimum branch coverage
  
  # Complexity Limits
  max_cyclomatic_complexity: 10  # Maximum function complexity
  max_cognitive_complexity: 15   # Maximum cognitive complexity
  max_method_length: 50          # Maximum lines per method
  max_class_length: 500          # Maximum lines per class
  
  # Security Requirements
  security_level: "strict"       # strict, moderate, or basic
  allow_security_warnings: false # Block on security warnings
  require_dependency_scan: true  # Require dependency vulnerability scan
  
  # Code Quality Metrics  
  min_maintainability_index: 70  # Microsoft maintainability index
  max_technical_debt_ratio: 5    # Maximum debt percentage
  max_duplication_ratio: 3       # Maximum code duplication
  
  # Style and Documentation
  require_docstrings: true       # Require public method documentation
  enforce_style_guide: true      # Enforce style guide compliance
  max_line_length: 88           # Maximum line length
  
  # Performance Thresholds
  max_response_time: 1000       # Maximum response time in ms
  max_memory_usage: 512         # Maximum memory usage in MB
```

### Pass/Fail Criteria
- **APPROVED**: All quality gates pass, no critical issues
- **NEEDS CHANGES**: Quality gate failures or critical issues present
- **REJECTED**: Severe security vulnerabilities or architectural violations

## Integration Points

### Workflow Integration
- **Phase 9 Integration**: Automatically invoked by WorkflowManager in Phase 9
- **PR Automation**: Triggered on pull request creation and updates
- **Commit Hooks**: Optional integration with pre-commit and pre-push hooks
- **CI/CD Pipeline**: Seamless integration with continuous integration systems

### Tool Integration
- **Static Analysis Tools**: ruff, mypy, bandit, eslint, golint, etc.
- **Testing Frameworks**: pytest, jest, go test with coverage reporting
- **Security Scanners**: bandit, semgrep, CodeQL, security linters
- **Documentation Tools**: pydoc, jsdoc, godoc for documentation validation

### External Service Integration
- **GitHub**: Pull request review comments and status checks
- **SonarQube**: Code quality metrics and technical debt tracking
- **Snyk**: Dependency vulnerability scanning and remediation
- **Code Climate**: Maintainability and test coverage analysis

## Review Execution Process

### Analysis Pipeline
1. **Preparation Phase**
   - Clone/fetch target repository and branch
   - Install project dependencies and dev tools
   - Configure analysis tools and custom rules
   - Validate review scope and targets

2. **Static Analysis Phase**
   - Run linting tools (ruff, eslint, golint)
   - Execute type checking (mypy, TypeScript)
   - Perform security scanning (bandit, semgrep)
   - Calculate complexity metrics

3. **Dynamic Analysis Phase**
   - Execute test suite with coverage analysis
   - Run performance benchmarks if configured
   - Validate documentation generation
   - Check build and deployment processes

4. **Review Synthesis Phase**
   - Aggregate results from all analysis tools
   - Apply quality gate validation
   - Generate prioritized issue list
   - Create actionable recommendations

5. **Reporting Phase**
   - Generate comprehensive review report
   - Create GitHub PR comments and reviews
   - Update external service integrations
   - Archive review results and metrics

## Configuration and Customization

### Project-Specific Configuration
```yaml
# .gadugi/code-review-config.yaml
review_settings:
  default_language: python
  review_scope: [src, tests, docs]
  exclude_patterns: ["*.generated.py", "migrations/*"]
  
tools:
  python:
    linters: [ruff, mypy, bandit]
    formatters: [black, isort]
    test_runner: pytest
    coverage_tool: coverage
    
  javascript:
    linters: [eslint, typescript]
    formatters: [prettier]
    test_runner: jest
    
quality_profiles:
  development:
    min_coverage: 70
    max_complexity: 15
    security_level: moderate
    
  production:
    min_coverage: 90
    max_complexity: 10
    security_level: strict

review_automation:
  auto_approve_threshold: 95    # Auto-approve if score >= 95
  auto_request_changes: 70      # Auto-request changes if score < 70
  create_follow_up_issues: true # Create issues for non-blocking items
```

### Custom Rule Development
- **Rule Templates**: Standard templates for common custom rules
- **Rule Testing**: Framework for validating custom rule effectiveness
- **Rule Documentation**: Automatic documentation generation for custom rules
- **Rule Sharing**: Mechanism for sharing rules across projects and teams

## Performance and Scalability

### Optimization Features
- **Incremental Analysis**: Only analyze changed files and their dependencies
- **Parallel Processing**: Concurrent execution of different analysis tools
- **Caching**: Cache analysis results for unchanged files and dependencies
- **Smart Filtering**: Focus analysis on high-risk and high-impact areas

### Resource Management
- **Memory Optimization**: Efficient memory usage for large codebases
- **Time Limits**: Configurable timeouts for analysis operations
- **Resource Quotas**: CPU and memory limits for analysis processes
- **Batch Processing**: Process multiple files efficiently

## Error Handling and Recovery

### Robust Analysis
- **Tool Failure Recovery**: Continue analysis if individual tools fail
- **Partial Results**: Return partial results when complete analysis fails
- **Retry Logic**: Intelligent retry for transient failures
- **Graceful Degradation**: Reduce analysis scope if resource constraints

### Quality Assurance
- **Result Validation**: Validate analysis results for consistency
- **False Positive Detection**: Machine learning-based false positive reduction
- **Confidence Scoring**: Provide confidence levels for identified issues
- **Human Review Integration**: Seamless handoff to human reviewers when needed

## Success Criteria

### Quality Metrics
- Catch 95%+ of critical code quality issues
- Maintain <5% false positive rate for security vulnerabilities
- Complete analysis within 5 minutes for typical PR size
- Achieve 90%+ developer satisfaction with review quality

### Integration Success
- Seamless integration with existing development workflows
- Zero-configuration setup for standard project types  
- Comprehensive documentation and troubleshooting guides
- Reliable operation across different project sizes and types

This agent ensures consistent, high-quality code throughout the development lifecycle while integrating seamlessly with existing tools and workflows.