# Security Patterns and Vulnerabilities


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

This document outlines security vulnerabilities to check for during code reviews.

## Input Validation Vulnerabilities

### SQL Injection
**Pattern**: Unsafe database query construction
**Detection**:
- String concatenation in SQL queries
- User input directly embedded in queries
- Dynamic query building without parameters

**Bad Examples**:
```python
# NEVER: Direct string interpolation
query = f"SELECT * FROM users WHERE id = {user_id}"

# NEVER: String concatenation
query = "SELECT * FROM users WHERE name = '" + username + "'"
```

**Good Examples**:
```python
# Good: Parameterized queries
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# Good: ORM with parameters
User.objects.filter(id=user_id)
```

### Command Injection
**Pattern**: Unsafe system command execution
**Detection**:
- `os.system()` with user input
- `subprocess` without proper escaping
- Shell commands with string formatting

**Bad Examples**:
```python
# DANGEROUS: Direct command injection
os.system(f"rm {user_provided_filename}")

# DANGEROUS: Shell injection
subprocess.run(f"grep {pattern} {filename}", shell=True)
```

**Safe Alternatives**:
```python
# Safe: Use lists instead of shell=True
subprocess.run(["grep", pattern, filename])

# Safe: Validate and sanitize input
if re.match(r'^[a-zA-Z0-9._-]+$', filename):
    subprocess.run(["rm", filename])
```

### Path Traversal
**Pattern**: Unsafe file path handling
**Detection**:
- Direct user input in file paths
- Missing path validation
- Relative path components (`../`)

**Bad Examples**:
```python
# DANGEROUS: Path traversal
with open(f"uploads/{user_filename}") as f:
    content = f.read()
```

**Safe Patterns**:
```python
# Safe: Validate and restrict paths
import os.path
safe_filename = os.path.basename(user_filename)
safe_path = os.path.join("uploads", safe_filename)
if os.path.commonpath([safe_path, "uploads"]) == "uploads":
    with open(safe_path) as f:
        content = f.read()
```

### XML External Entity (XXE)
**Pattern**: Unsafe XML parsing
**Detection**:
- XML parsers without entity restriction
- External entity processing enabled

**Safe XML Parsing**:
```python
# Safe: Disable external entities
from defusedxml import ElementTree as ET
tree = ET.parse(xml_file)  # Safe by default
```

## Authentication and Authorization Issues

### Weak Password Policies
**Pattern**: Insufficient password requirements
**Detection**:
- No minimum length requirements
- No complexity requirements
- Plain text password storage

**Good Practices**:
```python
import bcrypt
import secrets

# Strong password hashing
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Secure token generation
reset_token = secrets.token_urlsafe(32)
```

### Session Management Issues
**Pattern**: Insecure session handling
**Detection**:
- Predictable session IDs
- Session fixation vulnerabilities
- Missing session timeouts

**Secure Session Management**:
```python
# Use secure session configuration
session.configure(
    cookie_secure=True,
    cookie_httponly=True,
    cookie_samesite='Strict',
    timeout=3600  # 1 hour timeout
)
```

### Insufficient Access Controls
**Pattern**: Missing authorization checks
**Detection**:
- Direct object references without validation
- Missing role-based access controls
- Privilege escalation opportunities

**Example Checks**:
```python
# Always verify user permissions
def delete_document(user, document_id):
    document = Document.get(document_id)
    if not document.can_delete(user):
        raise PermissionDenied("Insufficient permissions")
    document.delete()
```

## Data Protection Issues

### Information Disclosure
**Pattern**: Exposing sensitive information
**Detection**:
- Detailed error messages in production
- Debug information leaking
- Sensitive data in logs

**Bad Examples**:
```python
# BAD: Exposing internal details
try:
    user = authenticate(username, password)
except DatabaseError as e:
    return f"Database error: {e}"  # Too detailed

# BAD: Logging sensitive data
logger.info(f"User {username} with password {password} logged in")
```

**Safe Patterns**:
```python
# Good: Generic error messages
try:
    user = authenticate(username, password)
except DatabaseError as e:
    logger.error(f"Database error: {e}")  # Log internally
    return "Authentication failed"  # Generic message

# Good: Sanitized logging
logger.info(f"User {username} logged in successfully")
```

### Insecure Cryptography
**Pattern**: Weak or incorrect crypto usage
**Detection**:
- Hardcoded encryption keys
- Weak algorithms (MD5, SHA1 for passwords)
- Custom crypto implementations

**Secure Crypto Patterns**:
```python
from cryptography.fernet import Fernet
import secrets

# Good: Secure key generation
key = Fernet.generate_key()
cipher = Fernet(key)

# Good: Secure random generation
nonce = secrets.token_bytes(16)
```

### Sensitive Data Exposure
**Pattern**: Unprotected sensitive information
**Detection**:
- Credit card numbers in plain text
- API keys in source code
- Personal data without encryption

## Web Application Security

### Cross-Site Scripting (XSS)
**Pattern**: Unsafe output encoding
**Detection**:
- Direct HTML output without escaping
- innerHTML with user data
- Unsafe template rendering

**Safe Patterns**:
```python
# Good: Use template auto-escaping
from jinja2 import Environment, select_autoescape

env = Environment(autoescape=select_autoescape(['html', 'xml']))

# Good: Explicit escaping
from html import escape
safe_output = escape(user_input)
```

### Cross-Site Request Forgery (CSRF)
**Pattern**: Missing CSRF protection
**Detection**:
- State-changing operations without tokens
- Missing CSRF middleware
- GET requests modifying data

**CSRF Protection**:
```python
# Ensure CSRF tokens are validated
@csrf_protect
def transfer_money(request):
    # This view is protected
    pass
```

### Security Headers Missing
**Pattern**: Missing security-related HTTP headers
**Check For**:
- Content-Security-Policy
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security

## API Security Issues

### Lack of Rate Limiting
**Pattern**: No request rate controls
**Detection**:
- API endpoints without throttling
- Missing rate limit headers
- No abuse protection

### Insufficient Input Validation
**Pattern**: APIs accepting invalid data
**Detection**:
- Missing input schema validation
- No size limits on uploads
- Accepting dangerous file types

**Good API Validation**:
```python
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    email = fields.Email(required=True)
    age = fields.Integer(validate=validate.Range(min=13, max=120))

schema = UserSchema()
result = schema.load(request_data)  # Validates input
```

## Common Security Anti-patterns

### Hardcoded Secrets
**Detection Patterns**:
- API keys in source files
- Database passwords in code
- Encryption keys as constants

**Example Issues**:
```python
# BAD: Hardcoded secrets
API_KEY = "sk_live_abc123xyz789"  # Never do this
DB_PASSWORD = "mypassword123"     # Never do this
```

### Debug Code in Production
**Detection Patterns**:
- Debug flags set to True
- Development endpoints enabled
- Verbose error reporting

### Unsafe Deserialization
**Pattern**: Deserializing untrusted data
**Detection**:
- `pickle.loads()` on user data
- `eval()` or `exec()` calls
- YAML unsafe loading

**Safe Alternatives**:
```python
# Safe: Use JSON instead of pickle
import json
data = json.loads(user_input)

# Safe: YAML safe loading
import yaml
data = yaml.safe_load(user_input)
```

## Security Testing Patterns

### Missing Security Tests
**Check For**:
- Authentication bypass tests
- Authorization tests
- Input validation tests
- HTTPS enforcement tests

### Example Security Tests
```python
def test_sql_injection_prevention():
    malicious_input = "'; DROP TABLE users; --"
    response = client.post("/search", {"query": malicious_input})
    # Should not cause database errors
    assert response.status_code != 500

def test_unauthorized_access():
    # Test access without proper permissions
    response = client.get("/admin/users")
    assert response.status_code == 403
```

## Environment and Configuration Security

### Insecure Defaults
**Pattern**: Production systems with development settings
**Detection**:
- Debug mode enabled
- Default passwords unchanged
- Unnecessary services running

### Configuration Exposure
**Pattern**: Sensitive config in accessible locations
**Detection**:
- `.env` files in web directories
- Config files with broad permissions
- Secrets in version control

## Third-party Dependencies

### Vulnerable Dependencies
**Pattern**: Using components with known vulnerabilities
**Detection**:
- Outdated package versions
- Dependencies with CVE reports
- Unmaintained packages

**Tools**: `safety check`, `snyk test`, `npm audit`

### Supply Chain Attacks
**Pattern**: Malicious or compromised dependencies
**Detection**:
- Unusual dependency additions
- Packages from unverified sources
- Dependencies with suspicious code

## Mobile and API Specific

### Insecure Data Storage
**Pattern**: Sensitive data in insecure locations
**Detection**:
- Unencrypted local databases
- Sensitive data in preferences
- Cache containing secrets

### Weak Server-Side Controls
**Pattern**: Over-reliance on client-side security
**Detection**:
- Authorization only on client
- Data validation only on client
- Security logic in client code

## Review Checklist by Severity

### Critical (Immediate Fix Required)
- [ ] SQL injection vulnerabilities
- [ ] Command injection possibilities
- [ ] Hardcoded secrets in code
- [ ] Authentication bypass issues
- [ ] Remote code execution risks

### High Priority
- [ ] XSS vulnerabilities
- [ ] CSRF missing protection
- [ ] Path traversal issues
- [ ] Insecure deserialization
- [ ] Missing access controls

### Medium Priority
- [ ] Weak cryptography usage
- [ ] Information disclosure
- [ ] Missing security headers
- [ ] Session management issues
- [ ] Input validation gaps

### Low Priority
- [ ] Missing rate limiting
- [ ] Insecure defaults
- [ ] Debug code remnants
- [ ] Dependency updates needed
- [ ] Security test coverage

## Context-Aware Security Reviews

### Application Type Considerations
- **Web Applications**: Focus on OWASP Top 10
- **APIs**: Emphasize authentication/authorization
- **Desktop Apps**: Check for local privilege escalation
- **Mobile Apps**: Verify data protection and transport security

### Industry-Specific Requirements
- **Financial**: PCI DSS compliance
- **Healthcare**: HIPAA compliance
- **Government**: FISMA requirements
- **General**: GDPR/privacy considerations

### Risk-Based Prioritization
- **Public-facing**: Higher scrutiny for input validation
- **Internal tools**: Focus on access controls
- **High-value targets**: Extra cryptography review
- **Legacy systems**: Gradual security improvements
