# Create Comprehensive Type Fix Agent

## Context
Create a specialized agent that can deeply understand and systematically fix Python type checking errors identified by pyright. The Gadugi project currently has 6,794 type issues (1,042 errors + 5,710 warnings) that need systematic resolution.

## Requirements

### 1. Agent Specialization
Create a dedicated `type-fix-agent` that:
- Understands pyright error messages and their root causes
- Has comprehensive knowledge of Python typing system
- Contains automated scripts and tools for bulk fixes
- Includes procedures for different classes of type errors
- Provides validation and testing after fixes

### 2. Core Capabilities
The agent must handle these error categories:
- **Import Errors**: Missing imports, circular dependencies
- **Missing Type Annotations**: Function parameters, return types, class attributes
- **Unknown Types**: Unresolved type references, incorrect generic usage
- **Protocol Violations**: Abstract method implementations, interface compliance
- **Type Compatibility**: Argument type mismatches, return type inconsistencies

### 3. Automated Tools
Include these automated fixing capabilities:
- Basic type annotation addition (str, int, bool, etc.)
- Import statement generation and optimization
- Generic type parameter inference
- Common pattern recognition and fixing
- Type stub generation for external dependencies

### 4. Documentation Integration
Reference and integrate with:
- Python typing documentation (typing module, PEP 484, 526, 544, etc.)
- Pyright configuration and error codes
- Type checking best practices
- Common type patterns in the Gadugi codebase

### 5. Validation Framework
Provide tools for:
- Running pyright after fixes to validate improvements
- Ensuring functionality is preserved (tests still pass)
- Measuring progress (error count reduction)
- Rollback capabilities for problematic fixes

## Implementation Strategy

### Phase 1: Agent Creation
- Create the type-fix-agent with comprehensive knowledge base
- Include automated fixing scripts and validation tools
- Document all supported error types and fix procedures

### Phase 2: Analysis and Categorization
- Run comprehensive pyright analysis
- Categorize all 6,794 issues by type and complexity
- Create priority order for fixes (imports → core → tests)

### Phase 3: Automated Fixes
- Apply automated fixes for common patterns
- Validate each batch of fixes
- Measure progress and document improvements

### Phase 4: Manual Intervention
- Handle complex type issues requiring human insight
- Fix protocol implementations and interface compliance
- Resolve circular dependencies and architectural issues

## Success Criteria
- Reduce pyright errors from 1,042 to under 50
- Reduce pyright warnings from 5,710 to under 500
- Maintain 100% test pass rate throughout process
- Create comprehensive type fixing procedures for future use
- Document all fixes and patterns for team knowledge

## Deliverables
1. Complete type-fix-agent implementation
2. Automated type fixing scripts and tools
3. Comprehensive error analysis and categorization
4. Priority-ordered fix implementation plan
5. Validation framework and progress tracking
6. Documentation of all fixes and patterns applied
