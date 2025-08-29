# Replace Hardcoded Secrets with Environment Variables

## Overview
Security improvement task to replace all hardcoded secrets in Docker Compose and Neo4j client configurations with environment variables. This ensures sensitive credentials are not exposed in the codebase.

## Problem Statement
Currently, the codebase contains hardcoded secrets including:
- Neo4j password "gadugi123" in docker-compose.yml files
- Potentially other hardcoded credentials in client configurations
- No environment variable template for developers

This poses security risks and makes it difficult to manage different environments.

## Technical Analysis

### Files to Update
1. **docker-compose.yml** - Main Docker Compose configuration
2. **.claude/orchestrator/docker-compose.yml** - Orchestrator Docker Compose (if exists)
3. **Neo4j client code** - Any files connecting to Neo4j with hardcoded credentials
4. **Configuration files** - Any other files with hardcoded secrets

### Implementation Strategy
- Use Docker Compose environment variable substitution
- Implement environment variable reading in Neo4j client code
- Create .env.example template file
- Update documentation with setup instructions
- Maintain backward compatibility where possible

## Implementation Plan

### Phase 1: Analysis
- Scan codebase for all hardcoded secrets
- Identify all Neo4j connection points
- Document current credential usage patterns

### Phase 2: Environment Setup
- Create .env.example with all required variables
- Define clear naming conventions for environment variables
- Set default values where appropriate

### Phase 3: Docker Compose Updates
- Replace hardcoded Neo4j password with ${NEO4J_PASSWORD}
- Update any other hardcoded values
- Ensure proper environment variable interpolation

### Phase 4: Client Code Updates
- Update Neo4j client to read from environment variables
- Add fallback mechanisms for development
- Implement proper error handling for missing variables

### Phase 5: Documentation
- Update README with environment setup instructions
- Document all required environment variables
- Add troubleshooting guide

## Testing Requirements

### Unit Tests
- Test environment variable reading logic
- Test fallback mechanisms
- Test error handling for missing variables

### Integration Tests
- Verify Docker Compose starts with environment variables
- Test Neo4j connectivity with new configuration
- Ensure all existing tests pass

### Security Tests
- Verify no secrets are logged
- Ensure .env file is properly gitignored
- Check for any remaining hardcoded values

## Success Criteria
1. ✅ All hardcoded secrets removed from codebase
2. ✅ Docker Compose files use environment variables
3. ✅ Neo4j client reads credentials from environment
4. ✅ .env.example file created with clear documentation
5. ✅ All tests pass with new configuration
6. ✅ Documentation updated with setup instructions
7. ✅ No breaking changes for existing deployments

## Implementation Steps

### Step 1: Create Issue
Create GitHub issue to track this security improvement work.

### Step 2: Create Feature Branch
Branch from feature/gadugi-v0.3-regeneration: `feature/replace-hardcoded-secrets-[issue-number]`

### Step 3: Audit Codebase
Search for all occurrences of hardcoded secrets:
- "gadugi123"
- "password"
- "secret"
- "token"
- "key"

### Step 4: Create .env.example
```bash
# Neo4j Configuration
NEO4J_PASSWORD=your_secure_password_here
NEO4J_AUTH=neo4j/your_secure_password_here
NEO4J_HOST=localhost
NEO4J_BOLT_PORT=7687
NEO4J_HTTP_PORT=7474

# Add other environment variables as needed
```

### Step 5: Update docker-compose.yml
Replace hardcoded values with environment variable references.

### Step 6: Update Neo4j Client
Modify client code to read from environment variables with proper fallbacks.

### Step 7: Update Documentation
- Add environment setup section to README
- Document all environment variables
- Include security best practices

### Step 8: Test Everything
- Run all unit tests
- Run integration tests
- Manual testing with different configurations
- Security audit

### Step 9: Create Pull Request
Create PR targeting feature/gadugi-v0.3-regeneration with comprehensive description.

### Step 10: Code Review
Ensure thorough review of security implications and implementation.

## Workflow Execution Notes
- Target branch: feature/gadugi-v0.3-regeneration (NOT main)
- Priority: High (security improvement)
- Estimated time: 2-3 hours
- Dependencies: None
- Risk: Low (with proper testing)

## Security Considerations
- Never commit actual .env files
- Use strong, unique passwords in production
- Rotate credentials regularly
- Document security best practices
- Consider using secret management tools for production

## Additional Notes
This is a critical security improvement that will:
- Improve security posture by removing hardcoded secrets
- Make the application more portable across environments
- Follow industry best practices for secret management
- Enable easier deployment configuration
