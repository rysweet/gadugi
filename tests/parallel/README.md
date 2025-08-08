# Parallel Execution Test Suite

This directory contains test scripts for verifying parallel execution capabilities of the orchestrator system.

## Test Scripts

### test_parallel_task_3.py
- **Purpose**: Writes timestamps to temporary files to verify concurrent execution
- **Output Files**:
  - `/tmp/parallel-task-3.txt` - Start timestamp
  - `/tmp/parallel-task-3-done.txt` - Completion timestamp (after 3-second delay)
- **Usage**: `python3 tests/parallel/test_parallel_task_3.py`

## Running Tests

Individual test execution:
```bash
python3 tests/parallel/test_parallel_task_3.py
```

## Verification

Check the output files to confirm execution:
```bash
cat /tmp/parallel-task-3.txt
cat /tmp/parallel-task-3-done.txt
```

The timestamps in these files can be compared with other parallel tasks to verify concurrent execution.
