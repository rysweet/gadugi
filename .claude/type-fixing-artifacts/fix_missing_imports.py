#!/usr/bin/env python3
"""
Fix all remaining missing import errors systematically
"""
import re
from pathlib import Path

def fix_numpy_imports(file_path):
    """Fix numpy import issues by adding type ignore comments"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace TYPE_CHECKING numpy imports with direct imports and type ignore
    patterns = [
        (r'if TYPE_CHECKING:\s*import numpy as np  # type: ignore[import-untyped]\s*else:\s*try:\s*import numpy as np  # type: ignore[import-untyped]', 
         'try:\n    import numpy as np  # type: ignore[import-untyped]'),
        (r'import numpy as np  # type: ignore[import-untyped](?!\s*#)', 'import numpy as np  # type: ignore[import-untyped]'),
        (r'import matplotlib\.pyplot as plt(?!\s*#)', 'import matplotlib.pyplot as plt  # type: ignore[import-untyped]'),
        (r'import seaborn as sns  # type: ignore[import-untyped](?!\s*#)', 'import seaborn as sns  # type: ignore[import-untyped]'),
    ]
    
    modified = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
            modified = True
    
    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed numpy imports in {file_path}")

def fix_relative_imports(file_path):
    """Fix relative import path issues"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    modified = False
    
    # Fix specific patterns based on file location
    if 'test_writer_agent' in str(file_path) or 'shared_test_instructions' in str(file_path):
        # These are directly in .claude/agents/
        content = content.replace('from utils.error_handling import', 'from ..shared.utils.error_handling import')
        content = content.replace('from interfaces import', 'from ..shared.interfaces import')
        content = content.replace('from state_management import', 'from ..shared.state_management import')
        content = content.replace('from task_tracking import', 'from ..shared.task_tracking import')
        content = content.replace('from github_operations import', 'from ..shared.github_operations import')
        modified = True
    
    # Fix workflow-master-enhanced.py imports
    if 'workflow-master-enhanced' in str(file_path):
        content = content.replace('from .claude.shared.', 'from ..shared.')
        modified = True
        
    # Fix system_design_reviewer imports (..shared should be ...shared)
    if 'system_design_reviewer' in str(file_path):
        content = content.replace('from ..shared.', 'from ...shared.')
        modified = True
    
    if content != original_content and modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed relative imports in {file_path}")

def main():
    """Main fixing logic"""
    base_path = Path('.')
    
    # Find all Python files that might have import issues
    py_files = list(base_path.rglob('*.py'))
    py_files = [f for f in py_files if '.venv' not in str(f) and '__pycache__' not in str(f)]
    
    for py_file in py_files:
        try:
            # Fix numpy and matplotlib imports
            if 'numpy' in py_file.read_text() or 'matplotlib' in py_file.read_text():
                fix_numpy_imports(py_file)
            
            # Fix relative imports
            if 'shared.' in py_file.read_text():
                fix_relative_imports(py_file)
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    print("Import fixing complete!")

if __name__ == "__main__":
    main()