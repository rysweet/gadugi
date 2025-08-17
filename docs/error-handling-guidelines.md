# Error Handling Guidelines

This document provides guidelines for proper error handling in the Gadugi project, including when error suppression is acceptable and how to implement robust error handling patterns.

## Best Practices for Error Handling

### 1. Always Handle Errors Explicitly

**DO:** Handle errors with proper logic
```bash
# Good - explicit error handling
if ! command; then
    echo "Error: Command failed"
    # Take appropriate action
    return 1
fi
```

**DON'T:** Blindly suppress errors
```bash
# Bad - error suppression without handling
command 2>/dev/null || true
```

### 2. Log Errors Before Handling

Always log what went wrong before taking action:

```bash
# Good - log then handle
if ! result=$(gh pr list 2>&1); then
    echo "Warning: Failed to query PRs: $result" >&2
    # Proceed with fallback or return error
fi
```

### 3. Use Appropriate Error Levels

- **ERROR**: Critical failures that stop execution
- **WARNING**: Issues that don't block progress but should be noted
- **INFO**: Diagnostic information that may help debugging

```bash
log() {
    local level="$1"
    local message="$2"
    echo "[$level] $(date '+%Y-%m-%d %H:%M:%S') - $message" >&2
}

log "ERROR" "Cannot continue - missing required file"
log "WARNING" "Optional feature unavailable"
log "INFO" "Starting process..."
```

## When Error Suppression is Acceptable

Error suppression should be rare and always justified with a comment. Acceptable cases include:

### 1. Cleanup Operations in Dockerfiles

When removing optional files during Docker image builds:

```dockerfile
# Acceptable - cleanup of optional files that may not exist
RUN find /usr -name "*.pyc" -delete \
    && find /usr -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null ; exit 0
```

**Justification**: These files may or may not exist, and their absence is not an error condition.

### 2. Diagnostic Commands in CI

When checking system state for informational purposes:

```yaml
# Acceptable - diagnostic output where failure is expected
- name: Check Docker status
  run: |
    docker --version
    # Diagnostic output - failure is expected if Docker not installed
    sudo systemctl status docker || true
```

**Justification**: The command is for diagnostic purposes only and failure doesn't affect the workflow.

### 3. Optional Feature Checks

When checking for optional features or tools:

```bash
# Acceptable - checking if optional label exists
if ! gh label list --json name | grep -q '"CreatedByTeamCoach"'; then
    gh label create "CreatedByTeamCoach" --color "7057ff"
fi
```

**Justification**: We explicitly check for existence before taking action.

## Error Handling Patterns

### Pattern 1: Try-Catch Style in Bash

```bash
# Try to execute command with error handling
execute_with_retry() {
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if command; then
            return 0
        fi

        echo "Attempt $attempt failed, retrying..." >&2
        ((attempt++))
        sleep 2
    done

    echo "All attempts failed" >&2
    return 1
}
```

### Pattern 2: Graceful Degradation

```bash
# Primary method with fallback
get_pr_data() {
    local pr_number="$1"

    # Try primary method
    if data=$(gh pr view "$pr_number" --json title,body 2>/dev/null); then
        echo "$data"
        return 0
    fi

    # Fallback to alternative method
    if data=$(git log --grep="PR #$pr_number" --format="%s" -1 2>/dev/null); then
        echo "{\"title\": \"$data\"}"
        return 0
    fi

    # No data available
    echo "{}"
    return 1
}
```

### Pattern 3: Error Context Preservation

```python
# Python example - preserve error context
try:
    result = perform_operation()
except SpecificError as e:
    # Log with context
    logger.error(f"Operation failed for item {item_id}: {e}")
    # Re-raise with additional context
    raise OperationError(f"Failed processing {item_id}") from e
```

### Pattern 4: Resource Cleanup

```bash
# Ensure cleanup happens even on error
cleanup() {
    local exit_code=$?

    # Always clean up temporary resources
    rm -f "$temp_file"

    # Restore original state
    cd "$original_dir"

    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT ERR INT TERM
```

## How to Audit for Error Suppressions

### 1. Find Error Suppressions in Shell Scripts

```bash
# Find common error suppression patterns
grep -r "2>/dev/null" --include="*.sh" .
grep -r "|| true" --include="*.sh" .
grep -r "|| :" --include="*.sh" .
grep -r "set +e" --include="*.sh" .
```

### 2. Find Error Suppressions in Python

```bash
# Find bare except clauses
grep -r "except:" --include="*.py" .

# Find broad exception handling
grep -r "except Exception" --include="*.py" .

# Find pass statements in exception handlers
grep -r "except.*:.*pass" --include="*.py" .
```

### 3. Find Error Suppressions in Dockerfiles

```bash
# Find error suppression in RUN commands
grep -r "|| true" --include="Dockerfile*" .
grep -r "2>/dev/null" --include="Dockerfile*" .
```

### 4. Validate Error Suppressions

For each suppression found:

1. **Check if it's justified**: Is there a comment explaining why?
2. **Consider alternatives**: Could this be handled explicitly?
3. **Add documentation**: If suppression is necessary, document why
4. **Test error paths**: Ensure the code behaves correctly when errors occur

## Adding Justification Comments

When error suppression is necessary, always add a clear comment:

```bash
# Good - justified suppression with comment
# Cleanup: Remove cache files that may not exist
find /tmp -name "*.cache" -delete 2>/dev/null || true

# Better - handle explicitly when possible
if [ -d /tmp ]; then
    find /tmp -name "*.cache" -delete 2>/dev/null || {
        echo "Note: Some cache files could not be removed"
    }
fi
```

## Testing Error Handling

### 1. Test Error Paths

Always test both success and failure paths:

```python
def test_operation_handles_failure():
    with pytest.raises(OperationError) as exc_info:
        perform_operation_with_invalid_input()

    assert "specific error message" in str(exc_info.value)
```

### 2. Test Recovery Mechanisms

```bash
# Test script with simulated failures
test_retry_logic() {
    # Simulate failures for first 2 attempts
    attempt=0
    mock_command() {
        ((attempt++))
        [ $attempt -ge 3 ]  # Succeed on 3rd attempt
    }

    # Should succeed after retries
    execute_with_retry mock_command
    assert_equals $? 0
}
```

### 3. Test Cleanup on Error

```python
def test_cleanup_on_error():
    temp_file = None
    try:
        temp_file = create_temp_file()
        # Force an error
        raise TestError("Simulated failure")
    except TestError:
        pass
    finally:
        # Verify cleanup happened
        assert not os.path.exists(temp_file)
```

## Summary

- **Never suppress errors without justification**
- **Always log errors before handling them**
- **Use appropriate error levels (ERROR/WARNING/INFO)**
- **Test error paths as thoroughly as success paths**
- **Document why when suppression is necessary**
- **Regularly audit codebase for hidden error suppressions**

Following these guidelines ensures robust, maintainable code that fails gracefully and provides clear diagnostics when issues occur.
