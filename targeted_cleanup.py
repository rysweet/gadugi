from typing import List, Set

import re

#!/usr/bin/env python3
"""
Targeted cleanup of issues introduced by systematic fixes.
"""
from pathlib import Path

class TargetedCleanup:
    def __init__(self):
        self.fixed_files = set()
        
    def run(self):
        """Main cleanup process."""
        print("Starting targeted cleanup...")
        
        # Step 1: Remove duplicate and unused imports
        print("\n=== Step 1: Cleaning up duplicate and unused imports ===")
        self.cleanup_imports()
        
        # Step 2: Fix syntax errors from import fixes
        print("\n=== Step 2: Fixing syntax errors ===")
        self.fix_syntax_errors()
        
        # Step 3: Consolidate import statements
        print("\n=== Step 3: Consolidating imports ===")
        self.consolidate_imports()
        
        print(f"\n=== Summary ===")
        print(f"Fixed files: {len(self.fixed_files)}")
        
    def cleanup_imports(self):
        """Remove duplicate and unused imports."""
        for py_file in Path('.').rglob('*.py'):
            if self.should_skip_file(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Remove duplicate imports
                lines = content.split('\n')
                seen_imports = set()
                cleaned_lines = []
                
                for line in lines:
                    # Track import lines to remove duplicates
                    if line.strip().startswith(('from ', 'import ')):
                        if line.strip() not in seen_imports:
                            seen_imports.add(line.strip())
                            cleaned_lines.append(line)
                        # Skip duplicate imports
                    else:
                        cleaned_lines.append(line)
                
                content = '\n'.join(cleaned_lines)
                
                # Remove empty lines between imports
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
                
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.fixed_files.add(str(py_file))
                    print(f"  Cleaned imports in {py_file}")
                    
            except Exception as e:
                print(f"  Error processing {py_file}: {e}")
                
    def fix_syntax_errors(self):
        """Fix syntax errors introduced by import fixes."""
        for py_file in Path('.').rglob('*.py'):
            if self.should_skip_file(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Fix common syntax issues
                fixes = [
                    # Fix empty import statements
                    (r'^from\s+[\w.]+\s+import\s*$', ''),
                    (r'^import\s*$', ''),
                    
                    # Fix malformed imports
                    (r'^from\s+([\w.]+)\s+import\s*\n', r'# TODO: Fix import from \1\n'),
                    
                    # Fix indentation after imports
                    (r'(\nfrom typing import [^\n]+\n)([A-Z])', r'\1\n\2'),
                ]
                
                for pattern, replacement in fixes:
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                
                # Clean up triple newlines
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
                
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.fixed_files.add(str(py_file))
                    print(f"  Fixed syntax in {py_file}")
                    
            except Exception as e:
                print(f"  Error processing {py_file}: {e}")
                
    def consolidate_imports(self):
        """Consolidate import statements for better organization."""
        for py_file in Path('.').rglob('*.py'):
            if self.should_skip_file(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                lines = content.split('\n')
                
                # Separate imports and other content
                imports = []
                other_lines = []
                in_imports = True
                
                for line in lines:
                    if line.strip().startswith(('from typing import', 'import ')):
                        if 'typing import' in line:
                            imports.append(line)
                        else:
                            imports.append(line)
                    elif line.strip().startswith(('from ', 'import ')) and in_imports:
                        imports.append(line)
                    elif line.strip() == '' and in_imports:
                        # Keep empty lines in import section
                        continue
                    else:
                        in_imports = False
                        other_lines.append(line)
                
                # Consolidate typing imports
                typing_imports = []
                other_imports = []
                
                for imp in imports:
                    if 'from typing import' in imp:
                        # Extract imported items
                        match = re.search(r'from typing import (.+)', imp)
                        if match:
                            items = [item.strip() for item in match.group(1).split(',')]
                            typing_imports.extend(items)
                    else:
                        other_imports.append(imp)
                
                # Rebuild file with consolidated imports
                new_lines = []
                
                # Add consolidated typing import if we have typing imports
                if typing_imports:
                    # Remove duplicates and sort
                    unique_typing = sorted(set(typing_imports))
                    if len(unique_typing) <= 5:
                        new_lines.append(f"from typing import {', '.join(unique_typing)}")
                    else:
                        # Multi-line for many imports
                        new_lines.append("from typing import (")
                        for i, item in enumerate(unique_typing):
                            if i == len(unique_typing) - 1:
                                new_lines.append(f"    {item}")
                            else:
                                new_lines.append(f"    {item},")
                        new_lines.append(")")
                    new_lines.append("")
                
                # Add other imports
                if other_imports:
                    new_lines.extend(other_imports)
                    new_lines.append("")
                
                # Add the rest of the file
                new_lines.extend(other_lines)
                
                new_content = '\n'.join(new_lines)
                
                # Only update if significantly different
                if len(new_content) != len(original_content) or \
                   original_content.count('from typing import') > 3:
                    py_file.write_text(new_content, encoding='utf-8')
                    self.fixed_files.add(str(py_file))
                    print(f"  Consolidated imports in {py_file}")
                    
            except Exception as e:
                print(f"  Error processing {py_file}: {e}")
                
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
            'analyze_pyright_errors.py',
            'fix_pyright_systematically.py',
        ]
        
        file_str = str(py_file)
        return any(pattern in file_str for pattern in skip_patterns)

if __name__ == "__main__":
    cleanup = TargetedCleanup()
    cleanup.run()