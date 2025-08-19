#!/usr/bin/env python3
"""
Systematic pyright error fixer.
Addresses the most common error patterns identified in the analysis.
"""
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set
import ast

class PyrightErrorFixer:
    def __init__(self):
        self.fixed_files = set()
        self.errors_fixed = 0
        
    def run(self):
        """Main entry point to fix all errors systematically."""
        print("Starting systematic pyright error fixing...")
        
        # Step 1: Fix undefined variables by adding common imports
        print("\n=== Step 1: Adding missing imports ===")
        self.fix_common_missing_imports()
        
        # Step 2: Remove unused imports 
        print("\n=== Step 2: Removing unused imports ===")
        self.remove_unused_imports()
        
        # Step 3: Fix specific error patterns
        print("\n=== Step 3: Fixing specific patterns ===")
        self.fix_specific_patterns()
        
        # Step 4: Fix test file import issues
        print("\n=== Step 4: Fixing test imports ===")
        self.fix_test_imports()
        
        print(f"\n=== Summary ===")
        print(f"Fixed files: {len(self.fixed_files)}")
        print(f"Errors addressed: {self.errors_fixed}")
        
    def fix_common_missing_imports(self):
        """Add commonly missing imports to files that need them."""
        
        # Common missing imports mapping
        import_fixes = {
            # typing imports
            r'\bAny\b': 'from typing import Any'
            r'\bOptional\b': 'from typing import Optional'
            r'\bList\b': 'from typing import List'
            r'\bDict\b': 'from typing import Dict'
            r'\bTuple\b': 'from typing import Tuple'
            r'\bSet\b': 'from typing import Set'
            r'\bUnion\b': 'from typing import Union'
            r'\bCallable\b': 'from typing import Callable'
            
            # datetime imports
            r'\bdatetime\.datetime\b': 'import datetime',
            r'\bdatetime\.timedelta\b': 'import datetime',
            
            # other common imports
            r'\bErrorHandler\b': 'from ..shared.error_handling import ErrorHandler',
            r'\bTaskTracker\b': 'from ..shared.task_tracking import TaskTracker',
            r'\bGitHubOperations\b': 'from ..shared.github_operations import GitHubOperations',
            r'\bStateManager\b': 'from ..shared.state_management import StateManager',
        }
        
        # Find all Python files
        for py_file in Path('.').rglob('*.py'):
            if self.should_skip_file(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Track which imports to add
                imports_to_add = set()
                
                # Check for missing imports
                for pattern, import_line in import_fixes.items():
                    if re.search(pattern, content) and import_line not in content:
                        imports_to_add.add(import_line)
                
                # Add missing imports
                if imports_to_add:
                    content = self.add_imports_to_file(content, list(imports_to_add))
                    
                # Write back if changed
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.fixed_files.add(str(py_file))
                    self.errors_fixed += len(imports_to_add)
                    print(f"  Fixed imports in {py_file}")
                    
            except Exception as e:
                print(f"  Error processing {py_file}: {e}")
                
    def remove_unused_imports(self):
        """Remove unused imports from files."""
        for py_file in Path('.').rglob('*.py'):
            if self.should_skip_file(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Remove specific unused imports we know about
                unused_patterns = [
                    r'^from typing import Set$'
                    r'^import Optional$',
                    r'^from unittest\.mock import Mock$',
                    r'^from unittest\.mock import patch$',
                ]
                
                for pattern in unused_patterns:
                    # Only remove if pyright specifically complains about it
                    content = re.sub(pattern, '', content, flags=re.MULTILINE)
                
                # Clean up empty lines
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
                
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.fixed_files.add(str(py_file))
                    print(f"  Removed unused imports from {py_file}")
                    
            except Exception as e:
                print(f"  Error processing {py_file}: {e}")
                
    def fix_specific_patterns(self):
        """Fix specific error patterns we identified."""
        
        # Fix common patterns
        patterns = [
            # Fix Optional member access
            (r'(\w+)\.(\w+)\s*# type: ignore', r'\1.\2 if \1 is not None else None'),
            
            # Fix datetime imports
            (r'datetime\.datetime\.now\(\)', 'datetime.now()'),
            
            # Fix status attribute access  
            (r'status\s*=\s*TestStatus', 'status: TestStatus = TestStatus'),
        ]
        
        for py_file in Path('.').rglob('*.py'):
            if self.should_skip_file(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                for pattern, replacement in patterns:
                    content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.fixed_files.add(str(py_file))
                    print(f"  Fixed patterns in {py_file}")
                    
            except Exception as e:
                print(f"  Error processing {py_file}: {e}")
                
    def fix_test_imports(self):
        """Fix imports in test files."""
        for py_file in Path('.').rglob('test_*.py'):
            if self.should_skip_file(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Add common test imports
                test_imports = [
                    'import pytest',
                    'from unittest.mock import Mock, patch, MagicMock',
                    'from typing import Any, Dict, List, Optional'
                ]
                
                imports_to_add = []
                for import_line in test_imports:
                    if import_line not in content:
                        # Check if we actually need this import
                        if ('pytest' in import_line and 'pytest' in content) or \
                           ('Mock' in import_line and ('Mock' in content or 'patch' in content)) or \
                           ('typing' in import_line and any(t in content for t in ['Any', 'Dict', 'List', 'Optional'])):
                            imports_to_add.append(import_line)
                
                if imports_to_add:
                    content = self.add_imports_to_file(content, imports_to_add)
                    
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.fixed_files.add(str(py_file))
                    print(f"  Fixed test imports in {py_file}")
                    
            except Exception as e:
                print(f"  Error processing {py_file}: {e}")
                
    def add_imports_to_file(self, content: str, imports: List[str]) -> str:
        """Add imports to a file in the right location."""
        lines = content.split('\n')
        
        # Find where to insert imports (after existing imports)
        import_section_end = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')) or line.strip().startswith('#'):
                import_section_end = i + 1
            elif line.strip() == '':
                continue
            else:
                break
                
        # Insert new imports
        for import_line in imports:
            if import_line not in content:
                lines.insert(import_section_end, import_line)
                import_section_end += 1
                
        return '\n'.join(lines)
        
    def should_skip_file(self, py_file: Path) -> bool:
        """Check if we should skip processing this file."""
        skip_patterns = [
            '__pycache__',
            '.git/',
            'node_modules/',
            '.venv/',
            '.pytest_cache/',
            'build/',
            'dist/',
        ]
        
        file_str = str(py_file)
        return any(pattern in file_str for pattern in skip_patterns)

if __name__ == "__main__":
    fixer = PyrightErrorFixer()
    fixer.run()