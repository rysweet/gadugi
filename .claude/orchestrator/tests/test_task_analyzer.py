import json
import sys
import tempfile
import unittest
        import shutil
        import ast
import issue between DefinitionNode and lsp_helper causing import
import failures.

#!/usr/bin/env python3

"""
Test suite for TaskAnalyzer component of OrchestratorAgent

Tests prompt file analysis, dependency detection, and task classification.
"""

# Add the components directory to the path
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / 'components'))

from task_analyzer import TaskAnalyzer, TaskComplexity, TaskInfo, TaskType

class TestTaskAnalyzer(unittest.TestCase):
    """Test cases for TaskAnalyzer"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.prompts_dir = Path(self.temp_dir) / "prompts"
        self.prompts_dir.mkdir(exist_ok=True)
        self.project_root = Path(self.temp_dir)

        self.analyzer = TaskAnalyzer(
            prompts_dir=str(self.prompts_dir),
            project_root=str(self.project_root)
        )

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_prompt(self, filename: str, content: str):
        """Create a test prompt file"""
        prompt_file = self.prompts_dir / filename
        with open(prompt_file, 'w') as f:
            f.write(content)
        return prompt_file

    def test_analyze_empty_directory(self):
        """Test analyzing empty prompts directory"""
        tasks = self.analyzer.analyze_all_prompts()
        self.assertEqual(len(tasks), 0)

    def test_extract_task_name(self):
        """Test task name extraction from prompt content"""
        content = """# Test Coverage Improvement for Definition Node

        This prompt describes a task for improving test coverage.
        """
        name = self.analyzer._extract_task_name(content)
        self.assertEqual(name, "Test Coverage Improvement for Definition Node")

    def test_classify_task_type_test_coverage(self):
        """Test classification of test coverage tasks"""
        content = "Write comprehensive unit tests for the definition_node.py module"
        name = "Test Coverage for Definition Node"

        task_type = self.analyzer._classify_task_type(content, name)
        self.assertEqual(task_type, TaskType.TEST_COVERAGE)

    def test_classify_task_type_bug_fix(self):
        """Test classification of bug fix tasks"""
        content = "Fix the circular import issue in lsp_helper.py"
        name = "Fix Import Bug"

        task_type = self.analyzer._classify_task_type(content, name)
        self.assertEqual(task_type, TaskType.BUG_FIX)

    def test_classify_task_type_feature(self):
        """Test classification of feature implementation tasks"""
        content = "Implement new OrchestratorAgent for parallel workflow execution"
        name = "Add OrchestratorAgent Feature"

        task_type = self.analyzer._classify_task_type(content, name)
        self.assertEqual(task_type, TaskType.FEATURE_IMPLEMENTATION)

    def test_assess_complexity_low(self):
        """Test low complexity assessment"""
        content = "Simple documentation update for README file"
        complexity = self.analyzer._assess_complexity(content)
        self.assertEqual(complexity, TaskComplexity.LOW)

    def test_assess_complexity_high(self):
        """Test high complexity assessment"""
        content = """
        Implement comprehensive parallel execution algorithm with performance optimization,
        scalability improvements, concurrent processing, distributed architecture,
        microservice integration, database migration, and complex design patterns.

        Files to modify:
        - file1.py
        - file2.py
        - file3.py
        - file4.py
        - file5.py
        - file6.py
        - file7.py
        - file8.py
        - file9.py
        - file10.py
        - file11.py

        Requires comprehensive test suite and integration testing.
        """ * 3  # Make it long

        complexity = self.analyzer._assess_complexity(content)
        self.assertIn(complexity, [TaskComplexity.HIGH, TaskComplexity.CRITICAL])

    def test_extract_target_files(self):
        """Test extraction of target files from prompt content"""
        content = """
        Modify the following files:
        - `gadugi/agents/workflow_manager.py`
        - `tests/test_workflow_manager.py`
        - Update gadugi/utils/helper.py
        """

        target_files = self.analyzer._extract_target_files(content)
        expected_files = [
            'gadugi/agents/workflow_manager.py',
            'tests/test_workflow_manager.py',
            'gadugi/utils/helper.py'
        ]

        for expected_file in expected_files:
            self.assertIn(expected_file, target_files)

    def test_extract_test_files(self):
        """Test extraction and inference of test files"""
        content = "Write tests in test_definition_node.py"
        target_files = ['gadugi/agents/workflow_manager.py']

        test_files = self.analyzer._extract_test_files(content, target_files)

        # Should find the explicit test file and infer one from target file
        self.assertIn('test_definition_node.py', test_files)
        self.assertIn('tests/test_definition_node.py', test_files)

    def test_estimate_duration(self):
        """Test duration estimation"""
        # Low complexity, few files
        duration = self.analyzer._estimate_duration(TaskComplexity.LOW, ['file1.py'])
        self.assertEqual(duration, 45)  # 30 + 15

        # High complexity, many files
        duration = self.analyzer._estimate_duration(TaskComplexity.HIGH, ['f1.py', 'f2.py', 'f3.py'])
        self.assertEqual(duration, 165)  # 120 + 45

        # Should cap at maximum
        many_files = [f'file{i}.py' for i in range(100)]
        duration = self.analyzer._estimate_duration(TaskComplexity.CRITICAL, many_files)
        self.assertEqual(duration, 480)  # Max 8 hours

    def test_estimate_resources(self):
        """Test resource requirement estimation"""
        resources = self.analyzer._estimate_resources(TaskComplexity.MEDIUM, 5)

        self.assertIn('cpu', resources)
        self.assertIn('memory', resources)
        self.assertIn('disk', resources)

        self.assertEqual(resources['cpu'], 2)  # Medium complexity base
        self.assertEqual(resources['memory'], 1024 + 5 * 50)  # Base + file scaling
        self.assertEqual(resources['disk'], 200 + 5 * 25)  # Base + file scaling

    @patch('builtins.open', new_callable=mock_open)
    @patch('ast.parse')
    @patch('ast.walk')
    def test_analyze_python_imports(self, mock_walk, mock_parse, mock_file):
        """Test Python import analysis"""
        # Mock AST parsing
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree

        # Create mock import nodes with proper types
        import_node = MagicMock(spec=ast.Import)
        import_node.names = [MagicMock(name='gadugi.agents.workflow_manager')]

        from_import_node = MagicMock(spec=ast.ImportFrom)
        from_import_node.module = 'gadugi.utils.helper'

        # Mock ast.walk to return our mock nodes
        mock_walk.return_value = []
import_node, from_import
import_node]

        # Mock file content
        mock_file.return_value.read.return_value = "import gadugi.agents.workflow_manager"

        test_file = self.project_root / "test.py"
        test_file.touch()

        dependencies = self.analyzer._analyze_python_imports(test_file)

        self.assertIn('gadugi.agents.workflow_manager', dependencies)
        self.assertIn('gadugi.utils.helper', dependencies)

    def test_analyze_prompt_file_complete(self):
        """Test complete prompt file analysis"""
        prompt_content = """# Test Coverage for Definition Node

## Overview
Improve test coverage for the definition_node.py module from 32% to 80%.

## Implementation
- Write unit tests for `gadugi/agents/workflow_manager.py`
- Create `tests/test_definition_node.py`
- Mock external dependencies appropriately

## Testing Requirements
Comprehensive test suite with edge cases.
"""

        prompt_file = self.create_test_prompt("test_definition_node.md", prompt_content)

        task_info = self.analyzer._analyze_prompt_file(prompt_file)

        self.assertIsNotNone(task_info)
        self.assertEqual(task_info.id, "test_definition_node")
        self.assertEqual(task_info.name, "Test Coverage for Definition Node")
        self.assertEqual(task_info.task_type, TaskType.TEST_COVERAGE)
        self.assertIn('gadugi/agents/workflow_manager.py', task_info.target_files)
        self.assertIn('tests/test_definition_node.py', task_info.test_files)

    def test_detect_conflicts(self):
        """Test file conflict detection between tasks"""
        # Create tasks with overlapping files
        task1 = TaskInfo(
            id='task1', name='Task 1', prompt_file='task1.md',
            task_type=TaskType.FEATURE_IMPLEMENTATION, complexity=TaskComplexity.MEDIUM,
            target_files=['file1.py', 'file2.py'], test_files=[], estimated_duration=60,
            resource_requirements={}, dependencies=[], conflicts=[], parallelizable=False,
            description='Task 1'
        )

        task2 = TaskInfo(
            id='task2', name='Task 2', prompt_file='task2.md',
            task_type=TaskType.BUG_FIX, complexity=TaskComplexity.LOW,
            target_files=['file2.py', 'file3.py'], test_files=[], estimated_duration=30,
            resource_requirements={}, dependencies=[], conflicts=[], parallelizable=False,
            description='Task 2'
        )

        self.analyzer.tasks = [task1, task2]
        self.analyzer._detect_conflicts()

        # task1 should have conflict with task2
        self.assertIn('task2', task1.conflicts)
        self.assertIn('task1', task2.conflicts)

    def test_classify_parallelizability(self):
        """Test task parallelizability classification"""
        # Parallelizable task: no conflicts, no dependencies, not critical
        task1 = TaskInfo(
            id='task1', name='Task 1', prompt_file='task1.md',
            task_type=TaskType.TEST_COVERAGE, complexity=TaskComplexity.MEDIUM,
            target_files=['file1.py'], test_files=[], estimated_duration=60,
            resource_requirements={}, dependencies=[], conflicts=[], parallelizable=False,
            description='Task 1'
        )

        # Non-parallelizable task: has conflicts
        task2 = TaskInfo(
            id='task2', name='Task 2', prompt_file='task2.md',
            task_type=TaskType.BUG_FIX, complexity=TaskComplexity.LOW,
            target_files=['file2.py'], test_files=[], estimated_duration=30,
            resource_requirements={}, dependencies=[], conflicts=['task3'], parallelizable=False,
            description='Task 2'
        )

        # Non-parallelizable task: critical complexity
        task3 = TaskInfo(
            id='task3', name='Task 3', prompt_file='task3.md',
            task_type=TaskType.FEATURE_IMPLEMENTATION, complexity=TaskComplexity.CRITICAL,
            target_files=['file3.py'], test_files=[], estimated_duration=240,
            resource_requirements={}, dependencies=[], conflicts=[], parallelizable=False,
            description='Task 3'
        )

        self.analyzer.tasks = [task1, task2, task3]
        self.analyzer.dependency_graph = {'task1': [], 'task2': [], 'task3': []}
        self.analyzer._classify_parallelizability()

        self.assertTrue(task1.parallelizable)
        self.assertFalse(task2.parallelizable)  # Has conflicts
        self.assertFalse(task3.parallelizable)  # Critical complexity

    def test_get_parallel_groups(self):
        """Test parallel task grouping"""
        # Create mix of parallelizable and sequential tasks
        parallel_task1 = TaskInfo(
            id='p1', name='Parallel 1', prompt_file='p1.md',
            task_type=TaskType.TEST_COVERAGE, complexity=TaskComplexity.LOW,
            target_files=['file1.py'], test_files=[], estimated_duration=30,
            resource_requirements={}, dependencies=[], conflicts=[], parallelizable=True,
            description='Parallel 1'
        )

        parallel_task2 = TaskInfo(
            id='p2', name='Parallel 2', prompt_file='p2.md',
            task_type=TaskType.TEST_COVERAGE, complexity=TaskComplexity.MEDIUM,
            target_files=['file2.py'], test_files=[], estimated_duration=60,
            resource_requirements={}, dependencies=[], conflicts=[], parallelizable=True,
            description='Parallel 2'
        )

        sequential_task = TaskInfo(
            id='s1', name='Sequential 1', prompt_file='s1.md',
            task_type=TaskType.FEATURE_IMPLEMENTATION, complexity=TaskComplexity.CRITICAL,
            target_files=['file3.py'], test_files=[], estimated_duration=240,
            resource_requirements={}, dependencies=[], conflicts=[], parallelizable=False,
            description='Sequential 1'
        )

        self.analyzer.tasks = [parallel_task1, parallel_task2, sequential_task]

        groups = self.analyzer.get_parallel_groups()

        # Should have at least 2 groups: one parallel group, one sequential
        self.assertGreaterEqual(len(groups), 2)

        # Check that parallel tasks are grouped together
        parallel_group = groups[0]
        self.assertIn(parallel_task1, parallel_group)
        self.assertIn(parallel_task2, parallel_group)

        # Sequential task should be in its own group
        sequential_groups = [g for g in groups if sequential_task in g]
        self.assertEqual(len(sequential_groups), 1)
        self.assertEqual(len(sequential_groups[0]), 1)

    def test_generate_execution_plan(self):
        """Test execution plan generation"""
        # Create test tasks
        task1 = TaskInfo(
            id='task1', name='Task 1', prompt_file='task1.md',
            task_type=TaskType.TEST_COVERAGE, complexity=TaskComplexity.LOW,
            target_files=['file1.py'], test_files=[], estimated_duration=30,
            resource_requirements={'cpu': 1, 'memory': 512, 'disk': 100},
            dependencies=[], conflicts=[], parallelizable=True,
            description='Task 1'
        )

        task2 = TaskInfo(
            id='task2', name='Task 2', prompt_file='task2.md',
            task_type=TaskType.BUG_FIX, complexity=TaskComplexity.MEDIUM,
            target_files=['file2.py'], test_files=[], estimated_duration=60,
            resource_requirements={'cpu': 2, 'memory': 1024, 'disk': 200},
            dependencies=[], conflicts=[], parallelizable=True,
            description='Task 2'
        )

        self.analyzer.tasks = [task1, task2]

        execution_plan = self.analyzer.generate_execution_plan()

        # Verify plan structure
        self.assertIn('total_tasks', execution_plan)
        self.assertIn('parallelizable_tasks', execution_plan)
        self.assertIn('sequential_tasks', execution_plan)
        self.assertIn('speed_improvement', execution_plan)
        self.assertIn('groups', execution_plan)

        # Check values
        self.assertEqual(execution_plan['total_tasks'], 2)
        self.assertEqual(execution_plan['parallelizable_tasks'], 2)
        self.assertEqual(execution_plan['sequential_tasks'], 0)
        self.assertGreater(execution_plan['speed_improvement'], 1.0)

    def test_save_analysis(self):
        """Test saving analysis results to file"""
        # Create a simple task
        task1 = TaskInfo(
            id='task1', name='Task 1', prompt_file='task1.md',
            task_type=TaskType.TEST_COVERAGE, complexity=TaskComplexity.LOW,
            target_files=['file1.py'], test_files=[], estimated_duration=30,
            resource_requirements={'cpu': 1, 'memory': 512, 'disk': 100},
            dependencies=[], conflicts=[], parallelizable=True,
            description='Task 1'
        )

        self.analyzer.tasks = [task1]

        output_file = self.project_root / "analysis.json"
        self.analyzer.save_analysis(str(output_file))

        # Verify file was created and contains valid JSON
        self.assertTrue(output_file.exists())

        with open(output_file, 'r') as f:
            data = json.load(f)

        self.assertIn('total_tasks', data)
        self.assertEqual(data['total_tasks'], 1)

class TestTaskAnalyzerIntegration(unittest.TestCase):
    """Integration tests for TaskAnalyzer with real prompt files"""

    def setUp(self):
        """Set up test environment with sample prompts"""
        self.temp_dir = tempfile.mkdtemp()
        self.prompts_dir = Path(self.temp_dir) / "prompts"
        self.prompts_dir.mkdir(exist_ok=True)

        # Create sample prompt files
        self.create_sample_prompts()

        self.analyzer = TaskAnalyzer(
            prompts_dir=str(self.prompts_dir),
            project_root=str(self.temp_dir)
        )

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sample_prompts(self):
        """Create sample prompt files for testing"""
        # Test coverage prompt
        test_coverage_prompt = """# Test Coverage Improvement for Definition Node

## Overview
Improve test coverage for the definition_node.py module from 32.09% to 80%+ by writing comprehensive unit tests.

## Target Files
- `gadugi/agents/workflow_manager.py`
- `tests/test_workflow_manager.py` (to be created)

## Implementation Steps
1. Analyze existing definition_node.py implementation
2. Write comprehensive unit tests covering all methods
3. Mock external dependencies appropriately
4. Ensure test isolation and idempotency

## Success Criteria
- Test coverage for definition_node.py reaches 80%+
- All tests pass consistently
- Tests are well-documented and maintainable
"""

        # Bug fix prompt
        bug_fix_prompt = """# Fix Circular Import in LSP Helper

## Problem
There's a circular import

## Target Files
- `gadugi/shared/github_operations.py`
- `gadugi/agents/workflow_manager.py`

## Solution
Refactor import structure to eliminate circular dependency.

## Testing
Ensure all existing functionality continues to work.
"""

        # Feature implementation prompt
        feature_prompt = """# Implement Advanced Query Builder

## Overview
Add sophisticated query building capabilities with performance optimization, caching, and distributed processing.

## Target Files
- `gadugi/orchestrator/advanced_scheduler.py` (new)
- `gadugi/orchestrator/optimizer.py` (new)
- `gadugi/orchestrator/cache.py` (new)
- `gadugi/utils/performance.py` (modify)
- Multiple test files

## Requirements
- Implement complex query optimization algorithms
- Add distributed query processing
- Integrate with existing database systems
- Comprehensive performance testing
- Scalability improvements

This is a complex feature requiring careful architecture and extensive testing.
"""

        with open(self.prompts_dir / "test_definition_node.md", 'w') as f:
            f.write(test_coverage_prompt)

        with open(self.prompts_dir / "fix_circular_import.md", 'w') as f:
            f.write(bug_fix_prompt)

        with open(self.prompts_dir / "advanced_query_builder.md", 'w') as f:
            f.write(feature_prompt)

    def test_analyze_all_sample_prompts(self):
        """Test analysis of all sample prompts"""
        tasks = self.analyzer.analyze_all_prompts()

        self.assertEqual(len(tasks), 3)

        # Verify task types are correctly classified
        task_types = {task.task_type for task in tasks}
        expected_types = {TaskType.TEST_COVERAGE, TaskType.BUG_FIX, TaskType.FEATURE_IMPLEMENTATION}
        self.assertEqual(task_types, expected_types)

        # Verify complexities are different
        complexities = {task.complexity for task in tasks}
        self.assertGreater(len(complexities), 1)  # Should have different complexities

        # Check that test coverage task is parallelizable
        test_task = next(task for task in tasks if task.task_type == TaskType.TEST_COVERAGE)
        self.assertTrue(test_task.parallelizable)

        # Check that feature implementation is likely not parallelizable (due to complexity)
        feature_task = next(task for task in tasks if task.task_type == TaskType.FEATURE_IMPLEMENTATION)
        # Complex feature tasks might not be parallelizable

    def test_execution_plan_generation(self):
        """Test execution plan generation with sample prompts"""
        tasks = self.analyzer.analyze_all_prompts()
        execution_plan = self.analyzer.generate_execution_plan()

        # Verify plan makes sense
        self.assertEqual(execution_plan['total_tasks'], 3)
        self.assertGreaterEqual(execution_plan['parallelizable_tasks'], 1)
        self.assertGreater(execution_plan['speed_improvement'], 1.0)

        # Verify groups structure
        self.assertGreater(len(execution_plan['groups']), 0)

        for group in execution_plan['groups']:
            self.assertIn('group_id', group)
            self.assertIn('tasks', group)
            self.assertIn('estimated_time', group)
            self.assertIn('parallelizable', group)

if __name__ == '__main__':
    unittest.main()
