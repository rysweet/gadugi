# Fix Type Errors in Container Runtime

## Objective
Fix all pyright type errors in the container runtime implementation files.

## Target Files
- container_runtime/image_manager.py (19 errors)
- container_runtime/container_manager.py (9 errors)
- container_runtime/audit_logger.py (several import and type errors)

## Focus Areas
1. **reportMissingImports**: Fix import paths for shared modules
2. **reportArgumentType**: Fix type mismatches in function calls
3. **reportCallIssue**: Fix incorrect function call signatures
4. **Path handling**: Properly handle Path | None types

## Strategy
1. Fix all import paths to use absolute imports from project root
2. Add proper None checks before using optional Path objects
3. Ensure Docker API calls have correct type annotations
4. Fix JSON serialization issues with custom types
5. Add type guards for runtime type checking

## Specific Fixes Needed
- Change relative imports to absolute (e.g., `from .claude.shared.error_handling import...`)
- Handle `Path | None` types with proper checks before file operations
- Add type annotations to all public methods
- Fix Docker client type annotations
- Ensure all error handlers have proper exception types

## Requirements
- Container functionality must remain unchanged
- Security policies must continue to work correctly
- All Docker operations must maintain current behavior
- Audit logging must continue to work properly
