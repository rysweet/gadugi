"""
OrchestratorAgent Utility Functions

This module contains utility functions for task analysis, file processing, 
and system resource management.
"""

import ast
import re
import json
import psutil
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class TaskAnalysisUtils:
    """Utilities for analyzing tasks and their dependencies."""
    
    @staticmethod
    def extract_target_files(prompt_content: str) -> List[str]:
        """Extract target files from prompt content."""
        files = []
        
        # Look for file paths in various formats
        patterns = [
            r'`([^`]+\.(py|js|ts|md|json|yaml|yml|toml))`',
            r'([a-zA-Z_][a-zA-Z0-9_/]*\.(py|js|ts|md|json|yaml|yml|toml))',
            r'src/[a-zA-Z_][a-zA-Z0-9_/]*\.(py|js|ts)',
            r'test[s]?/[a-zA-Z_][a-zA-Z0-9_/]*\.(py|js|ts)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, prompt_content, re.IGNORECASE)
            if isinstance(matches[0], tuple):
                files.extend([match[0] for match in matches])
            else:
                files.extend(matches)
        
        return list(set(files))  # Remove duplicates
    
    @staticmethod
    def parse_import_statement(line: str) -> Dict[str, Any]:
        """Parse a Python import statement."""
        line = line.strip()
        
        if line.startswith('from '):
            # from module import item1, item2
            match = re.match(r'from\s+([^\s]+)\s+import\s+(.+)', line)
            if match:
                module = match.group(1)
                items = [item.strip() for item in match.group(2).split(',')]
                return {
                    'type': 'from_import',
                    'module': module,
                    'items': items,
                    'raw': line
                }
        elif line.startswith('import '):
            # import module1, module2
            match = re.match(r'import\s+(.+)', line)
            if match:
                modules = [module.strip() for module in match.group(1).split(',')]
                return {
                    'type': 'import',
                    'modules': modules,
                    'raw': line
                }
        
        return {'type': 'unknown', 'raw': line}
    
    @staticmethod
    def analyze_file_dependencies(file_path: str) -> Dict[str, List[str]]:
        """Analyze file dependencies using AST parsing."""
        if not file_path.endswith('.py'):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            dependencies = {
                'imports': [],
                'from_imports': [],
                'local_imports': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if module.startswith('.'):
                        dependencies['local_imports'].append(module)
                    else:
                        dependencies['from_imports'].append(module)
            
            return dependencies
            
        except Exception as e:
            return {'error': str(e)}


class ResourceMonitor:
    """System resource monitoring utilities."""
    
    @staticmethod
    def get_system_state() -> Dict[str, Any]:
        """Get current system resource state."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'available_memory_gb': psutil.virtual_memory().available / (1024**3),
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def detect_resource_exhaustion(thresholds: Optional[Dict[str, float]] = None) -> bool:
        """Detect if system resources are exhausted."""
        if thresholds is None:
            thresholds = {
                'cpu_percent': 90.0,
                'memory_percent': 85.0,
                'disk_percent': 95.0
            }
        
        try:
            state = ResourceMonitor.get_system_state()
            
            # Check CPU
            if state.get('cpu_percent', 0) > thresholds['cpu_percent']:
                return True
            
            # Check Memory
            if state.get('memory_percent', 0) > thresholds['memory_percent']:
                return True
            
            # Check Disk
            if state.get('disk_percent', 0) > thresholds['disk_percent']:
                return True
            
            return False
            
        except Exception:
            # If we can't determine resource state, assume exhaustion
            return True


class PromptFileParser:
    """Parser for structured prompt files."""
    
    @staticmethod
    def parse_prompt_file(file_path: str) -> Dict[str, Any]:
        """Parse a structured prompt file and extract metadata."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter if present
            frontmatter = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        import yaml
                        frontmatter = yaml.safe_load(parts[1])
                        content = parts[2]
                    except ImportError:
                        pass
            
            # Extract sections
            sections = {}
            current_section = 'content'
            current_content = []
            
            for line in content.split('\n'):
                if line.startswith('# ') or line.startswith('## '):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                        current_content = []
                    current_section = line.strip('# ').lower().replace(' ', '_')
                else:
                    current_content.append(line)
            
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            return {
                'path': file_path,
                'frontmatter': frontmatter,
                'sections': sections,
                'target_files': TaskAnalysisUtils.extract_target_files(content)
            }
            
        except Exception as e:
            return {
                'path': file_path,
                'error': str(e),
                'frontmatter': {},
                'sections': {},
                'target_files': []
            }
    
    @staticmethod
    def extract_requirements(prompt_data: Dict[str, Any]) -> List[str]:
        """Extract requirements from parsed prompt data."""
        requirements = []
        
        # Look in common sections
        sections_to_check = [
            'requirements', 'feature_requirements', 
            'functional_requirements', 'implementation_plan'
        ]
        
        for section_name in sections_to_check:
            section = prompt_data['sections'].get(section_name, '')
            if section:
                # Extract bullet points and numbered lists
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith(('- ', '* ', '+ ')):
                        requirements.append(line[2:].strip())
                    elif re.match(r'^\d+\.', line):
                        requirements.append(re.sub(r'^\d+\.\s*', '', line))
        
        return requirements


class TaskIdGenerator:
    """Generate unique task identifiers."""
    
    @staticmethod
    def generate_task_id(prefix: str = "task") -> str:
        """Generate a unique task ID."""
        import uuid
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        unique_suffix = str(uuid.uuid4())[:8]
        
        return f"{prefix}-{timestamp}-{unique_suffix}"
    
    @staticmethod
    def is_valid_task_id(task_id: str) -> bool:
        """Validate a task ID format."""
        pattern = r'^[a-zA-Z]+-\d{8}-\d{6}-[a-f0-9]{8}$'
        return bool(re.match(pattern, task_id))


class FileSystemUtils:
    """File system utility functions."""
    
    @staticmethod
    def find_files_by_pattern(directory: str, patterns: List[str]) -> List[str]:
        """Find files matching patterns in directory."""
        import glob
        
        files = []
        for pattern in patterns:
            files.extend(glob.glob(os.path.join(directory, pattern), recursive=True))
        
        return list(set(files))
    
    @staticmethod
    def calculate_file_complexity(file_path: str) -> Dict[str, Any]:
        """Calculate basic complexity metrics for a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            metrics = {
                'total_lines': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()]),
                'comment_lines': len([line for line in lines if line.strip().startswith('#')]),
                'file_size_bytes': len(content.encode('utf-8')),
                'has_classes': 'class ' in content,
                'has_functions': 'def ' in content,
                'has_imports': any(line.strip().startswith(('import ', 'from ')) 
                                 for line in lines)
            }
            
            if file_path.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    metrics['ast_complexity'] = {
                        'classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                        'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                        'imports': len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
                    }
                except:
                    pass
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}


class ConfigurationManager:
    """Manage orchestration configuration."""
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load orchestration configuration."""
        default_config = {
            'max_parallel_tasks': 5,
            'resource_thresholds': {
                'cpu_percent': 80.0,
                'memory_percent': 75.0,
                'disk_percent': 90.0
            },
            'circuit_breaker': {
                'failure_threshold': 3,
                'recovery_timeout': 300
            },
            'retry_strategy': {
                'max_attempts': 3,
                'backoff_strategy': 'exponential',
                'base_delay': 1.0
            },
            'worktree_settings': {
                'cleanup_on_success': True,
                'preserve_on_failure': True,
                'base_directory': '.worktrees'
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Merge configurations
                def merge_dicts(default: dict, user: dict) -> dict:
                    result = default.copy()
                    for key, value in user.items():
                        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                            result[key] = merge_dicts(result[key], value)
                        else:
                            result[key] = value
                    return result
                
                return merge_dicts(default_config, user_config)
                
            except Exception as e:
                print(f"Error loading config from {config_path}: {e}")
                return default_config
        
        return default_config