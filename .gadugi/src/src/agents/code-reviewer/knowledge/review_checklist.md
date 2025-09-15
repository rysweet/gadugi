# Comprehensive Code Review Checklist


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

This document provides a systematic checklist for thorough code reviews, organized by priority and category.

## Pre-Review Setup

### Understanding the Change
- [ ] Read the PR description and linked issues
- [ ] Understand the business requirements
- [ ] Identify the scope of changes
- [ ] Check for breaking changes
- [ ] Review related documentation updates

### Context Gathering
- [ ] Review recent related changes
- [ ] Check for similar patterns in the codebase
- [ ] Understand the affected components
- [ ] Identify stakeholders and reviewers needed

## Critical Issues (Must Fix Before Merge)

### Security Vulnerabilities
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (proper output encoding)
- [ ] Command injection prevention (no shell=True with user input)
- [ ] Path traversal prevention (validate file paths)
- [ ] Authentication bypass checks
- [ ] Authorization verification for all endpoints
- [ ] Input validation on all user-provided data
- [ ] Cryptographic operations using secure libraries
- [ ] No hardcoded secrets or credentials
- [ ] Proper error handling without information leakage

### Data Integrity and Corruption Risks
- [ ] Database transactions are atomic
- [ ] Concurrent access properly handled
- [ ] Data validation prevents corruption
- [ ] Backup and recovery considerations
- [ ] Migration scripts are reversible
- [ ] Foreign key constraints preserved

### System Stability Issues
- [ ] No infinite loops or recursion without limits
- [ ] Resource cleanup (files, connections, memory)
- [ ] Exception handling prevents crashes
- [ ] Thread safety in concurrent code
- [ ] Graceful degradation under load
- [ ] Circuit breakers for external dependencies

## High Priority Issues (Should Fix)

### Code Quality and Maintainability
- [ ] Functions have single, clear responsibilities
- [ ] Classes follow SOLID principles
- [ ] Code duplication is minimized
- [ ] Magic numbers replaced with named constants
- [ ] Complex logic is broken into smaller functions
- [ ] Cyclomatic complexity is reasonable (<10 per function)

### Error Handling
- [ ] Specific exceptions caught rather than bare except
- [ ] Errors are logged appropriately
- [ ] User-facing error messages are helpful
- [ ] Resource cleanup in exception paths
- [ ] Fallback behavior for non-critical failures

### Performance Considerations
- [ ] No N+1 query problems
- [ ] Appropriate data structures used
- [ ] Database queries are optimized
- [ ] Large datasets processed efficiently
- [ ] Caching implemented where beneficial
- [ ] Unnecessary computations avoided

### Testing Requirements
- [ ] New functionality has unit tests
- [ ] Edge cases are covered
- [ ] Negative test cases included
- [ ] Integration tests for cross-component changes
- [ ] Test data is realistic and comprehensive
- [ ] Tests are deterministic and isolated

## Medium Priority Issues (Should Consider)

### Design and Architecture
- [ ] New code follows established patterns
- [ ] Abstractions are appropriate for complexity
- [ ] Dependencies are justified and minimal
- [ ] Interfaces are well-designed
- [ ] Code organization is logical
- [ ] Separation of concerns is maintained

### Documentation and Clarity
- [ ] Public APIs have docstrings
- [ ] Complex algorithms are commented
- [ ] README updated for significant changes
- [ ] Inline comments explain "why" not "what"
- [ ] Type hints provided (Python)
- [ ] Examples provided for complex usage

### Naming and Readability
- [ ] Variable names are descriptive
- [ ] Function names indicate their purpose
- [ ] Class names follow naming conventions
- [ ] Abbreviations are avoided or well-known
- [ ] Boolean variables/functions use is/has/can prefixes
- [ ] Constants are properly named and placed

### Configuration and Environment
- [ ] Configuration is externalized appropriately
- [ ] Environment-specific settings handled
- [ ] Default values are sensible
- [ ] Configuration validation implemented
- [ ] Secrets management follows best practices

## Low Priority Issues (Nice to Have)

### Code Style and Formatting
- [ ] Consistent indentation and spacing
- [ ] Line length follows project standards
- [ ] Import statements are organized
- [ ] Trailing whitespace removed
- [ ] Consistent quote style
- [ ] Code formatter (Black, Prettier) applied

### Minor Optimizations
- [ ] Unnecessary object creation avoided
- [ ] String concatenation optimized in loops
- [ ] Generator expressions used where appropriate
- [ ] List comprehensions used appropriately
- [ ] Functional programming patterns applied consistently

### Documentation Enhancements
- [ ] Code comments are current and accurate
- [ ] TODOs have issue numbers or deadlines
- [ ] API documentation is complete
- [ ] Usage examples are provided
- [ ] Changelog updated for user-facing changes

## Language-Specific Checks

### Python Specific
- [ ] Type hints provided for public APIs
- [ ] Context managers used for resource management
- [ ] Generator functions used for large datasets
- [ ] Proper use of `__init__.py` files
- [ ] Virtual environment dependencies updated
- [ ] F-strings used instead of format() where appropriate
- [ ] List/dict comprehensions are readable
- [ ] Exception chaining preserved (`raise from`)

### JavaScript/TypeScript Specific
- [ ] Async/await used instead of callback hell
- [ ] Promises handled with proper error catching
- [ ] Event listeners are properly removed
- [ ] Memory leaks prevented in closures
- [ ] TypeScript types are accurate and helpful
- [ ] Null/undefined checks are present

### SQL/Database Specific
- [ ] Indexes exist for query performance
- [ ] Joins are efficient and necessary
- [ ] Transactions have appropriate isolation levels
- [ ] Schema changes are backward compatible
- [ ] Data migration scripts tested

## Testing Checklist

### Unit Testing
- [ ] Test coverage is adequate (>80% for new code)
- [ ] Tests are focused and test one thing
- [ ] Test names describe what they verify
- [ ] Mocks are used appropriately
- [ ] Test data setup is clean and isolated
- [ ] Assertions are specific and meaningful

### Integration Testing
- [ ] API contracts are tested
- [ ] Database interactions are tested
- [ ] External service integrations have tests
- [ ] End-to-end workflows are covered
- [ ] Error scenarios are tested

### Test Quality
- [ ] Tests are deterministic
- [ ] Tests don't depend on external services
- [ ] Test data doesn't hardcode dates/times
- [ ] Tests clean up after themselves
- [ ] Flaky tests are identified and fixed

## Security Review Deep Dive

### Input Validation
- [ ] All inputs validated against expected format
- [ ] Size limits enforced on uploads/inputs
- [ ] Dangerous file types rejected
- [ ] Unicode handling is secure
- [ ] Regular expressions don't have ReDoS vulnerabilities

### Output Encoding
- [ ] HTML output is properly escaped
- [ ] JSON responses don't include sensitive data
- [ ] XML output prevents XXE attacks
- [ ] CSV output prevents formula injection

### Authentication and Authorization
- [ ] Password requirements are enforced
- [ ] Account lockout mechanisms exist
- [ ] Session management is secure
- [ ] Multi-factor authentication supported
- [ ] Password reset flows are secure
- [ ] Authorization checks can't be bypassed

### Data Protection
- [ ] Sensitive data is encrypted at rest
- [ ] Secure transmission (HTTPS/TLS)
- [ ] PII handling follows privacy regulations
- [ ] Data retention policies implemented
- [ ] Audit trails for sensitive operations

## Performance Review Deep Dive

### Database Performance
- [ ] Query plans reviewed for efficiency
- [ ] Indexes support common query patterns
- [ ] Bulk operations used instead of loops
- [ ] Connection pooling implemented
- [ ] Query timeouts configured
- [ ] Read replicas used for read-heavy operations

### Application Performance
- [ ] Caching strategies implemented
- [ ] Lazy loading used where appropriate
- [ ] Background jobs for long-running tasks
- [ ] Rate limiting implemented
- [ ] Resource usage monitored
- [ ] Performance benchmarks established

### Scalability Considerations
- [ ] Stateless design principles followed
- [ ] Horizontal scaling considerations
- [ ] Database sharding readiness
- [ ] Message queue patterns for async work
- [ ] CDN usage for static assets
- [ ] Auto-scaling triggers configured

## Deployment and Operations

### Monitoring and Observability
- [ ] Logging levels appropriate
- [ ] Metrics collection implemented
- [ ] Health checks available
- [ ] Error tracking configured
- [ ] Performance monitoring in place
- [ ] Alerting rules defined

### Configuration Management
- [ ] Feature flags used for risky changes
- [ ] Environment parity maintained
- [ ] Secrets rotation capability
- [ ] Configuration validation
- [ ] Rollback procedures documented

### Deployment Safety
- [ ] Database migrations are safe
- [ ] Backward compatibility maintained
- [ ] Canary deployment strategy
- [ ] Blue-green deployment ready
- [ ] Monitoring during deployment

## Review Process Guidelines

### Communication and Feedback
- [ ] Feedback is constructive and specific
- [ ] Suggestions include reasoning
- [ ] Praise for good practices included
- [ ] Questions asked for clarification
- [ ] Alternatives suggested when appropriate

### Review Efficiency
- [ ] Review completed within agreed timeframe
- [ ] Large PRs broken into smaller ones
- [ ] Automated checks passed before review
- [ ] Focus on significant issues first
- [ ] Follow-up items tracked appropriately

### Knowledge Sharing
- [ ] Learning opportunities identified
- [ ] Best practices shared
- [ ] Architecture decisions explained
- [ ] Code patterns documented
- [ ] Team conventions reinforced

## Post-Review Actions

### Before Merge
- [ ] All critical issues resolved
- [ ] Tests passing in CI/CD
- [ ] Documentation updated
- [ ] Required approvals obtained
- [ ] Merge conflicts resolved

### After Merge
- [ ] Deployment monitoring
- [ ] Performance impact verified
- [ ] User feedback collected
- [ ] Lessons learned documented
- [ ] Team practices updated if needed

## Context-Specific Considerations

### Early Development Phase
- Focus on: Architecture, security fundamentals, testing foundation
- De-emphasize: Perfect code style, minor optimizations
- Prioritize: Rapid iteration, learning, establishing patterns

### Mature Product
- Focus on: Backward compatibility, performance, maintainability
- Emphasize: Documentation, comprehensive testing, monitoring
- Prioritize: Stability, scalability, operational excellence

### Critical Systems
- Focus on: Security, reliability, auditability
- Emphasize: Thorough testing, error handling, monitoring
- Prioritize: Risk mitigation, compliance, disaster recovery

### Team Considerations
- **Junior developers**: Focus on learning and best practices
- **Senior developers**: Expect higher standards and innovation
- **Mixed team**: Balance mentoring with efficiency
- **Distributed team**: Extra emphasis on documentation

## Tools Integration Checklist

### Automated Checks
- [ ] Linting tools configured and passing
- [ ] Security scanners integrated
- [ ] Test coverage reporting enabled
- [ ] Performance benchmarks automated
- [ ] Dependency vulnerability scanning

### Review Tools
- [ ] PR templates used consistently
- [ ] Review assignments automated
- [ ] Status checks required before merge
- [ ] Review analytics tracked
- [ ] Knowledge base integration

This checklist should be adapted based on:
- Project requirements and constraints
- Team experience and capabilities
- Business criticality and risk tolerance
- Regulatory and compliance requirements
- Technical architecture and stack choices
