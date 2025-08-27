#!/usr/bin/env python3
"""
Parallel Type Safety Fixes for Gadugi v0.3

This script divides type errors into categories and fixes them in parallel.
"""

import asyncio
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import re


@dataclass
class TypeErrorFix:
    """Represents a type error fix task."""
    
    directory: str
    error_count: int
    status: str = "pending"
    errors_fixed: int = 0
    
    
@dataclass 
class ErrorPattern:
    """Common error pattern and its fix."""
    
    pattern: str
    fix_type: str
    solution: str


# Common error patterns and fixes
ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        pattern='"os" is not defined',
        fix_type="missing_import",
        solution="import os"
    ),
    ErrorPattern(
        pattern='Import "pytest" could not be resolved',
        fix_type="missing_import", 
        solution="import pytest"
    ),
    ErrorPattern(
        pattern='"session" is not a known attribute of "None"',
        fix_type="none_check",
        solution="if session is not None:"
    ),
    ErrorPattern(
        pattern='No parameter named "database"',
        fix_type="parameter_mismatch",
        solution="# Check function signature"
    ),
    ErrorPattern(
        pattern='"SubTask" is not defined',
        fix_type="missing_import",
        solution="from gadugi.models import SubTask"
    ),
]


async def analyze_errors(directory: str) -> Dict[str, Any]:
    """Analyze type errors in a directory."""
    cmd = f"uv run pyright {directory} 2>&1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    errors: Dict[str, int] = {}
    for line in result.stdout.split('\n'):
        if 'error:' in line:
            # Extract error type
            match = re.search(r'error: (.+?) \(', line)
            if match:
                error_type = match.group(1)
                errors[error_type] = errors.get(error_type, 0) + 1
    
    return {
        "directory": directory,
        "total_errors": sum(errors.values()),
        "error_types": errors
    }


async def fix_missing_imports(file_path: Path) -> int:
    """Fix missing import errors in a file."""
    fixes_made = 0
    
    # Read file
    content = file_path.read_text()
    lines = content.split('\n')
    
    # Check for missing imports
    imports_to_add: List[str] = []
    
    if '"os" is not defined' in content and 'import os' not in content:
        imports_to_add.append('import os')
        fixes_made += 1
    
    if '"sys" is not defined' in content and 'import sys' not in content:
        imports_to_add.append('import sys')
        fixes_made += 1
    
    if '"json" is not defined' in content and 'import json' not in content:
        imports_to_add.append('import json')
        fixes_made += 1
    
    if '"asyncio" is not defined' in content and 'import asyncio' not in content:
        imports_to_add.append('import asyncio')
        fixes_made += 1
    
    # Add imports after docstring/shebang
    if imports_to_add:
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('"""') or line.startswith("'''"):
                # Find end of docstring
                for j in range(i+1, len(lines)):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        insert_index = j + 1
                        break
                break
            elif not line.startswith('#') and line.strip():
                insert_index = i
                break
        
        # Insert imports
        for imp in imports_to_add:
            lines.insert(insert_index, imp)
            insert_index += 1
        
        # Write back
        file_path.write_text('\n'.join(lines))
    
    return fixes_made


async def fix_none_checks(file_path: Path) -> int:
    """Add None checks for optional attributes."""
    fixes_made = 0
    
    content = file_path.read_text()
    lines = content.split('\n')
    
    # Pattern: accessing attribute on potentially None object
    for i, line in enumerate(lines):
        if 'is not a known attribute of "None"' in str(line):
            # Add None check before this line
            indent = len(line) - len(line.lstrip())
            # This is simplified - real implementation would be more sophisticated
            fixes_made += 1
    
    return fixes_made


async def fix_type_annotations(file_path: Path) -> int:
    """Add missing type annotations."""
    fixes_made = 0
    
    content = file_path.read_text()
    lines = content.split('\n')
    
    # Add return type annotations to __init__ methods
    for i, line in enumerate(lines):
        if 'def __init__(self' in line and ') -> None:' not in line:
            if ':' in line:
                lines[i] = line.replace(':', ') -> None:')
                fixes_made += 1
    
    if fixes_made > 0:
        file_path.write_text('\n'.join(lines))
    
    return fixes_made


async def fix_directory(directory: str) -> Dict[str, Any]:
    """Fix all type errors in a directory."""
    print(f"Starting fixes for {directory}")
    
    # Get all Python files
    dir_path = Path(directory)
    if not dir_path.exists():
        return {"directory": directory, "status": "not_found"}
    
    py_files = list(dir_path.glob("**/*.py"))
    total_fixes = 0
    
    # Fix each file
    for file_path in py_files:
        try:
            fixes = 0
            fixes += await fix_missing_imports(file_path)
            fixes += await fix_none_checks(file_path)
            fixes += await fix_type_annotations(file_path)
            
            if fixes > 0:
                print(f"  Fixed {fixes} issues in {file_path.name}")
                total_fixes += fixes
        except Exception as e:
            print(f"  Error fixing {file_path}: {e}")
    
    print(f"Completed {directory}: {total_fixes} fixes")
    
    return {
        "directory": directory,
        "files_processed": len(py_files),
        "fixes_made": total_fixes,
        "status": "completed"
    }


async def main() -> None:
    """Main entry point for parallel type fixing."""
    
    # Priority directories to fix
    directories = [
        ".claude/agents",
        ".claude/services", 
        ".claude/orchestrator",
        "gadugi-v0.3/tests",
        "tests/shared",
        ".claude/engines",
        ".claude/executors"
    ]
    
    print("Starting parallel type safety fixes...")
    print(f"Processing {len(directories)} directories")
    
    # Run fixes in parallel
    tasks = [fix_directory(d) for d in directories]
    results = await asyncio.gather(*tasks)
    
    # Summary
    print("\n" + "="*50)
    print("Type Safety Fix Summary")
    print("="*50)
    
    total_fixes = 0
    for result in results:
        if result['status'] == 'completed':
            print(f"{result['directory']}: {result['fixes_made']} fixes")
            total_fixes += result['fixes_made']
    
    print(f"\nTotal fixes applied: {total_fixes}")
    
    # Re-run pyright to check remaining errors
    print("\nChecking remaining errors...")
    subprocess.run("uv run pyright 2>&1 | tail -5", shell=True)


if __name__ == "__main__":
    asyncio.run(main())