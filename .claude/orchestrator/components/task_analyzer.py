#!/usr/bin/env python3
"""
TaskAnalyzer Component for OrchestratorAgent

Analyzes prompt files to identify parallelizable tasks, detect dependencies,
and create execution plans for optimal parallel workflow execution.

Security Features:
- Input validation for all file paths and content
- Resource limits to prevent system overload
- Sanitized output to prevent injection attacks
"""

import ast
import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

# Security: Define maximum limits to prevent resource exhaustion
MAX_PROMPT_FILES = 50
MAX_FILE_SIZE_MB = 10
MAX_PARALLEL_TASKS = 8
ALLOWED_FILE_EXTENSIONS = {'.md', '.txt', '.py', '.js', '.json'}

# Configure secure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TaskComplexity(Enum):
    """Task complexity classification"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskType(Enum):
    """Task type classification"""
    TEST_COVERAGE = "test_coverage"
    BUG_FIX = "bug_fix"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"


@dataclass
class TaskInfo:
    """Comprehensive task information"""
    id: str
    name: str
    prompt_file: str
    task_type: TaskType
    complexity: TaskComplexity
    target_files: List[str]
    test_files: List[str]
    estimated_duration: int  # minutes
    resource_requirements: Dict[str, int]
    dependencies: List[str]
    conflicts: List[str]
    parallelizable: bool
    description: str


class TaskAnalyzer:
    """Analyzes prompt files and creates execution plans"""

    def __init__(self, prompts_dir: Optional[str] = None, project_root: str = ".") -> None:
        # Security: Validate and sanitize input paths
        self.project_root = self._validate_directory_path(project_root)
        # If prompts_dir not specified, use project_root/prompts
        if prompts_dir is None:
            self.prompts_dir = self.project_root / "prompts"
        else:
            self.prompts_dir = self._validate_directory_path(prompts_dir)
        self.tasks: List[TaskInfo] = []
        self.dependency_graph: Dict[str, List[str]] = {}
        self.conflict_matrix: Dict[str, Set[str]] = {}

    def _validate_directory_path(self, path: str) -> Path:
        """Security: Validate directory paths to prevent path traversal attacks"""
        try:
            resolved_path = Path(path).resolve()
            # Prevent path traversal attacks - but allow relative paths that resolve to absolute
            if '..' in Path(path).parts:  # Check original path for .. components
                raise ValueError(f"Path traversal detected: {path}")
            return resolved_path
        except Exception as e:
            logging.error(f"Path validation failed for {path}: {e}")
            raise ValueError(f"Invalid directory path: {path}")

    def _validate_file_path(self, file_path: str) -> Path:
        """Security: Validate file paths and extensions"""
        try:
            path = Path(file_path).resolve()

            # Check file extension
            if path.suffix not in ALLOWED_FILE_EXTENSIONS:
                raise ValueError(f"Unsupported file extension: {path.suffix}")

            # Check file size
            if path.exists() and path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise ValueError(f"File too large: {path}")

            # Prevent path traversal
            if '..' in str(path):
                raise ValueError(f"Path traversal attempt detected: {file_path}")

            return path
        except Exception as e:
            logging.error(f"File validation failed for {file_path}: {e}")
            raise ValueError(f"Invalid file path: {file_path}")

    def _sanitize_content(self, content: str) -> str:
        """Security: Sanitize file content to prevent injection attacks"""

        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
        ]

        sanitized = content
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

        return sanitized

    def analyze_prompts(self, prompt_files: List[str]) -> List[TaskInfo]:
        """Analyze specific prompt files for parallel execution

        Args:
            prompt_files: List of prompt file paths to analyze (relative to prompts_dir or absolute)

        Returns:
            List of TaskInfo objects with dependency and conflict analysis
        """
        # Security: Validate input parameters

        if len(prompt_files) > MAX_PROMPT_FILES:
            raise ValueError(f"Too many prompt files. Maximum allowed: {MAX_PROMPT_FILES}")

        print(f"🔍 Analyzing {len(prompt_files)} prompt files for parallel execution opportunities...")

        if not prompt_files:
            print("⚠️  No prompt files provided to analyze")
            return []

        self.tasks = []
        for prompt_file_path in prompt_files:
            try:
                # Security: Validate file path
                validated_path = self._validate_file_path(prompt_file_path)

                # Handle both relative and absolute paths
                if os.path.isabs(prompt_file_path):
                    prompt_file = validated_path
                else:
                    prompt_file = self.prompts_dir / prompt_file_path
                    prompt_file = self._validate_file_path(str(prompt_file))

                if not prompt_file.exists():
                    print(f"⚠️  Prompt file not found: {prompt_file}")
                    continue

            except ValueError as e:
                logging.warning(f"Skipping invalid prompt file {prompt_file_path}: {e}")
                continue

            # Skip already implemented prompts (based on markers or history)
            if self._is_already_implemented(prompt_file):
                print(f"⏭️  Skipping already implemented: {prompt_file.name}")
                continue

            try:
                task_info = self._analyze_prompt_file(prompt_file)
                if task_info:
                    self.tasks.append(task_info)
                    print(f"✅ Analyzed: {task_info.name} ({task_info.task_type.value})")
            except Exception as e:
                print(f"⚠️  Failed to analyze {prompt_file}: {e}")

        # Build dependency and conflict relationships
        self._build_dependency_graph()
        self._detect_conflicts()
        self._classify_parallelizability()

        print(f"📊 Analysis complete: {len(self.tasks)} tasks analyzed")
        return self.tasks

    def _is_already_implemented(self, prompt_file: Path) -> bool:
        """Check if a prompt has already been implemented

        This could check for:
        - Completed marker in the prompt file
        - Corresponding PR/issue closed
        - Git history showing implementation
        """
        # Simple check: look for "IMPLEMENTED" marker in file
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if "IMPLEMENTED" in first_line or "COMPLETED" in first_line:
                    return True
        except:
            pass

        # Check for corresponding closed issue/PR (if pattern is predictable)
        # Example: test-definition-node.md -> issue with "definition-node" in title
        # This would require GitHub API access

        return False

    def _analyze_prompt_file(self, prompt_file: Path) -> Optional[TaskInfo]:
        """Analyze a single prompt file"""
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract basic information
        task_id = prompt_file.stem
        name = self._extract_task_name(content)
        task_type = self._classify_task_type(content, name)
        complexity = self._assess_complexity(content)

        # Extract technical details
        target_files = self._extract_target_files(content)
        test_files = self._extract_test_files(content, target_files)
        dependencies = self._extract_dependencies(content, target_files)

        # Estimate resources
        estimated_duration = self._estimate_duration(complexity, target_files)
        resource_requirements = self._estimate_resources(complexity, len(target_files))

        # Extract description
        description = self._extract_description(content)

        return TaskInfo(
            id=task_id,
            name=name,
            prompt_file=str(prompt_file),
            task_type=task_type,
            complexity=complexity,
            target_files=target_files,
            test_files=test_files,
            estimated_duration=estimated_duration,
            resource_requirements=resource_requirements,
            dependencies=dependencies,
            conflicts=[],  # Will be populated by _detect_conflicts
            parallelizable=False,  # Will be determined by _classify_parallelizability
            description=description
        )

    def _extract_task_name(self, content: str) -> str:
        """Extract task name from prompt content"""
        # Look for main heading
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()

        # Fallback to first non-empty line
        for line in lines:
            if line.strip():
                return line.strip()[:50]

        return "Unknown Task"

    def _classify_task_type(self, content: str, name: str) -> TaskType:
        """Classify the type of task based on content analysis"""
        content_lower = content.lower()
        name_lower = name.lower()

        # Score different task types to pick the most likely one
        scores = {
            TaskType.TEST_COVERAGE: 0,
            TaskType.BUG_FIX: 0,
            TaskType.FEATURE_IMPLEMENTATION: 0,
            TaskType.REFACTORING: 0,
            TaskType.DOCUMENTATION: 0,
            TaskType.CONFIGURATION: 0
        }

        # Test coverage indicators (must be strong indicators)
        test_indicators = [
            'test coverage', 'unit test', 'integration test', 'pytest',
            'write tests', 'test suite', 'coverage improvement'
        ]
        for indicator in test_indicators:
            if indicator in content_lower or indicator in name_lower:
                scores[TaskType.TEST_COVERAGE] += 3

        # Look for test-specific patterns
        if 'test_' in content_lower or 'test_' in name_lower:
            scores[TaskType.TEST_COVERAGE] += 2
        if 'coverage' in name_lower:
            scores[TaskType.TEST_COVERAGE] += 2

        # Bug fix indicators
        bug_indicators = ['fix', 'bug', 'error', 'issue', 'problem', 'broken', 'circular import']
        for indicator in bug_indicators:
            if indicator in content_lower or indicator in name_lower:
                scores[TaskType.BUG_FIX] += 2

        # Feature implementation indicators
        feature_indicators = ['implement', 'add', 'create', 'new feature', 'build']
        for indicator in feature_indicators:
            if indicator in content_lower or indicator in name_lower:
                scores[TaskType.FEATURE_IMPLEMENTATION] += 2

        # Refactoring indicators
        refactor_indicators = ['refactor', 'improve', 'optimize', 'restructure', 'cleanup']
        for indicator in refactor_indicators:
            if indicator in content_lower or indicator in name_lower:
                scores[TaskType.REFACTORING] += 2

        # Documentation indicators
        doc_indicators = ['documentation', 'docs', 'readme', 'guide', 'tutorial']
        for indicator in doc_indicators:
            if indicator in content_lower or indicator in name_lower:
                scores[TaskType.DOCUMENTATION] += 2

        # Configuration indicators
        config_indicators = ['config', 'setup', 'configure', 'settings', 'environment']
        for indicator in config_indicators:
            if indicator in content_lower or indicator in name_lower:
                scores[TaskType.CONFIGURATION] += 2

        # Return the highest scoring type, or default to feature implementation
        max_score = max(scores.values())
        if max_score == 0:
            return TaskType.FEATURE_IMPLEMENTATION

        # Find the type with the highest score
        for task_type, score in scores.items():
            if score == max_score:
                return task_type

        return TaskType.FEATURE_IMPLEMENTATION  # Fallback

    def _assess_complexity(self, content: str) -> TaskComplexity:
        """Assess task complexity based on content analysis"""
        # Count indicators of complexity
        complexity_score = 0

        # Length indicator
        word_count = len(content.split())
        if word_count > 2000:
            complexity_score += 2
        elif word_count > 1000:
            complexity_score += 1

        # Technical complexity indicators
        complex_keywords = [
            'algorithm', 'optimization', 'performance', 'scalability',
            'architecture', 'design pattern', 'concurrent', 'parallel',
            'distributed', 'microservice', 'database', 'migration'
        ]
        complexity_score += sum(1 for keyword in complex_keywords if keyword in content.lower())

        # Number of files mentioned
        file_mentions = len(re.findall(r'\w+\.(py|js|ts|java|cpp|c|h)(?:\w)*', content))
        if file_mentions > 10:
            complexity_score += 2
        elif file_mentions > 5:
            complexity_score += 1

        # Testing requirements
        if 'comprehensive test' in content.lower() or 'test suite' in content.lower():
            complexity_score += 1

        # Integration requirements
        if any(word in content.lower() for word in ['integration', 'api', 'external']):
            complexity_score += 1

        # Classify based on score
        if complexity_score >= 6:
            return TaskComplexity.CRITICAL
        elif complexity_score >= 4:
            return TaskComplexity.HIGH
        elif complexity_score >= 2:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.LOW

    def _extract_target_files(self, content: str) -> List[str]:
        """Extract target files that will be modified"""
        target_files = []

        # Find Python file references
        python_files = re.findall(r'(\w+(?:/\w+)*\.py)', content)
        target_files.extend(python_files)

        # Find specific file paths
        file_paths = re.findall(r'`([^`]+\.(py|js|ts|md|json|yaml|yml))`', content)
        target_files.extend([path[0] for path in file_paths])

        # Look for directory references (currently unused but may be needed for future enhancements)

        # Remove duplicates and clean paths
        cleaned_files = []
        seen = set()
        for file_path in target_files:
            # Clean and normalize path
            clean_path = file_path.strip('`"\'').replace('\\', '/')
            if clean_path and clean_path not in seen:
                cleaned_files.append(clean_path)
                seen.add(clean_path)

        return cleaned_files

    def _extract_test_files(self, content: str, target_files: List[str]) -> List[str]:
        """Extract or infer test files for the task"""
        test_files = []

        # Direct test file references
        test_patterns = [
            r'test_\w+\.py',
            r'\w+_test\.py',
            r'tests?/\w+\.py'
        ]

        for pattern in test_patterns:
            test_files.extend(re.findall(pattern, content))

        # Infer test files from target files
        for target_file in target_files:
            if target_file.endswith('.py') and not target_file.startswith('test_'):
                # Infer corresponding test file
                base_name = Path(target_file).stem
                test_file = f"tests/test_{base_name}.py"
                if test_file not in test_files:
                    test_files.append(test_file)

        return test_files

    def _extract_dependencies(self, content: str, target_files: List[str]) -> List[str]:
        """Extract task dependencies"""
        dependencies = []

        # Look for explicit dependencies
        dep_patterns = [
            r'depends on (\w+)',
            r'requires (\w+)',
            r'after (\w+)',
            r'prerequisite.*?(\w+)'
        ]

        for pattern in dep_patterns:
            dependencies.extend(re.findall(pattern, content, re.IGNORECASE))

        # Analyze import dependencies for target files
        for target_file in target_files:
            file_path = self.project_root / target_file
            if file_path.exists() and target_file.endswith('.py'):
                deps = self._analyze_python_imports(file_path)
                dependencies.extend(deps)

        return list(set(dependencies))  # Remove duplicates

    def _analyze_python_imports(self, file_path: Path) -> List[str]:
        """Analyze Python imports to detect dependencies"""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse Python imports
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('gadugi'):
                            dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('gadugi'):
                        dependencies.append(node.module)

        except (SyntaxError, FileNotFoundError):
            pass  # Skip files that can't be parsed

        return dependencies

    def _estimate_duration(self, complexity: TaskComplexity, target_files: List[str]) -> int:
        """Estimate task duration in minutes"""
        base_duration = {
            TaskComplexity.LOW: 30,
            TaskComplexity.MEDIUM: 60,
            TaskComplexity.HIGH: 120,
            TaskComplexity.CRITICAL: 240
        }

        duration = base_duration[complexity]

        # Add time for each target file
        duration += len(target_files) * 15

        # Cap at reasonable maximum
        return min(duration, 480)  # Max 8 hours

    def _estimate_resources(self, complexity: TaskComplexity, file_count: int) -> Dict[str, int]:
        """Estimate resource requirements"""
        base_resources = {
            TaskComplexity.LOW: {'cpu': 1, 'memory': 512, 'disk': 100},
            TaskComplexity.MEDIUM: {'cpu': 2, 'memory': 1024, 'disk': 200},
            TaskComplexity.HIGH: {'cpu': 3, 'memory': 2048, 'disk': 500},
            TaskComplexity.CRITICAL: {'cpu': 4, 'memory': 4096, 'disk': 1000}
        }

        resources = base_resources[complexity].copy()

        # Scale with file count
        resources['memory'] += file_count * 50
        resources['disk'] += file_count * 25

        return resources

    def _extract_description(self, content: str) -> str:
        """Extract task description"""
        lines = content.split('\n')

        # Look for overview or description section
        description_lines = []
        in_description = False

        for line in lines:
            if line.lower().strip().startswith(('## overview', '## description', '## summary')):
                in_description = True
                continue
            elif line.startswith('##') and in_description:
                break
            elif in_description and line.strip():
                description_lines.append(line.strip())

        if description_lines:
            return ' '.join(description_lines)[:200] + ('...' if len(' '.join(description_lines)) > 200 else '')

        # Fallback to first paragraph
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if len(paragraph.strip()) > 50:
                return paragraph.strip()[:200] + ('...' if len(paragraph.strip()) > 200 else '')

        return "No description available"

    def _build_dependency_graph(self):
        """Build task dependency graph"""
        self.dependency_graph = {}

        for task in self.tasks:
            self.dependency_graph[task.id] = []

            # Add explicit dependencies
            for dep in task.dependencies:
                # Find matching tasks
                for other_task in self.tasks:
                    if (dep.lower() in other_task.name.lower() or
                        dep.lower() in other_task.id.lower() or
                        any(dep.lower() in f.lower() for f in other_task.target_files)):
                        self.dependency_graph[task.id].append(other_task.id)

    def _detect_conflicts(self):
        """Detect file conflicts between tasks"""
        self.conflict_matrix = {}

        for i, task1 in enumerate(self.tasks):
            self.conflict_matrix[task1.id] = set()

            for j, task2 in enumerate(self.tasks):
                if i != j:
                    # Check for file overlaps
                    overlap = set(task1.target_files) & set(task2.target_files)
                    if overlap:
                        if task1.id not in self.conflict_matrix:
                            self.conflict_matrix[task1.id] = set()
                        self.conflict_matrix[task1.id].add(task2.id)
                        task1.conflicts.append(task2.id)

    def _classify_parallelizability(self):
        """Classify tasks as parallelizable or sequential"""
        for task in self.tasks:
            # Task is parallelizable if:
            # 1. No file conflicts with other tasks
            # 2. No dependencies on other tasks
            # 3. Not a critical complexity task requiring sequential attention

            has_conflicts = len(task.conflicts) > 0
            has_dependencies = len(self.dependency_graph.get(task.id, [])) > 0
            is_critical = task.complexity == TaskComplexity.CRITICAL

            task.parallelizable = not (has_conflicts or has_dependencies or is_critical)

    def get_parallel_groups(self) -> List[List[TaskInfo]]:
        """Group parallelizable tasks into execution batches"""
        parallel_tasks = [task for task in self.tasks if task.parallelizable]
        sequential_tasks = [task for task in self.tasks if not task.parallelizable]

        groups = []

        # Group parallel tasks by type and complexity for balanced execution
        if parallel_tasks:
            # Sort by estimated duration for load balancing
            parallel_tasks.sort(key=lambda t: t.estimated_duration, reverse=True)

            # Create balanced groups (max 4 tasks per group for system resources)
            current_group = []
            for task in parallel_tasks:
                if len(current_group) < 4:
                    current_group.append(task)
                else:
                    groups.append(current_group)
                    current_group = [task]

            if current_group:
                groups.append(current_group)

        # Add sequential tasks as individual groups
        for task in sequential_tasks:
            groups.append([task])

        return groups

    def generate_execution_plan(self) -> Dict:
        """Generate comprehensive execution plan"""
        parallel_groups = self.get_parallel_groups()

        total_sequential_time = sum(task.estimated_duration for task in self.tasks)

        # Calculate parallel execution time
        parallel_time = 0
        for group in parallel_groups:
            # Time for this group is the longest task in the group
            group_time = max(task.estimated_duration for task in group) if group else 0
            parallel_time += group_time

        speed_improvement = total_sequential_time / max(parallel_time, 1)

        return {
            'total_tasks': len(self.tasks),
            'parallelizable_tasks': len([t for t in self.tasks if t.parallelizable]),
            'sequential_tasks': len([t for t in self.tasks if not t.parallelizable]),
            'execution_groups': len(parallel_groups),
            'estimated_sequential_time': total_sequential_time,
            'estimated_parallel_time': parallel_time,
            'speed_improvement': round(speed_improvement, 2),
            'resource_requirements': self._calculate_total_resources(),
            'groups': [
                {
                    'group_id': i,
                    'tasks': [asdict(task) for task in group],
                    'estimated_time': max(task.estimated_duration for task in group) if group else 0,
                    'parallelizable': len(group) > 1 and all(task.parallelizable for task in group)
                }
                for i, group in enumerate(parallel_groups)
            ]
        }

    def _calculate_total_resources(self) -> Dict[str, int]:
        """Calculate total resource requirements"""
        total = {'cpu': 0, 'memory': 0, 'disk': 0}

        for task in self.tasks:
            for resource, amount in task.resource_requirements.items():
                total[resource] = max(total.get(resource, 0), amount)

        return total

    def save_analysis(self, output_file: str):
        """Save analysis results to JSON file"""
        execution_plan = self.generate_execution_plan()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(execution_plan, f, indent=2, default=str)

        print(f"📄 Analysis saved to: {output_file}")


def main():
    """CLI entry point for TaskAnalyzer"""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze prompt files for parallel execution")
    parser.add_argument("--prompts-dir", default="/prompts/", help="Directory containing prompt files")
    parser.add_argument("--output", default="task_analysis.json", help="Output file for analysis results")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    analyzer = TaskAnalyzer(args.prompts_dir)

    try:
        # Get all prompt files in the directory
        prompt_files = [f for f in os.listdir(args.prompts_dir)
                       if f.endswith('.md') and os.path.isfile(os.path.join(args.prompts_dir, f))]
        tasks = analyzer.analyze_prompts(prompt_files)
        execution_plan = analyzer.generate_execution_plan()

        print(f"\n📝 Analyzed {len(tasks)} tasks")

        print(f"\n📊 Analysis Summary:")
        print(f"Total tasks: {execution_plan['total_tasks']}")
        print(f"Parallelizable: {execution_plan['parallelizable_tasks']}")
        print(f"Sequential: {execution_plan['sequential_tasks']}")
        print(f"Speed improvement: {execution_plan['speed_improvement']}x")
        print(f"Sequential time: {execution_plan['estimated_sequential_time']} minutes")
        print(f"Parallel time: {execution_plan['estimated_parallel_time']} minutes")

        analyzer.save_analysis(args.output)

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
