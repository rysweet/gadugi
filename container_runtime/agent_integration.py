"""
Agent-Manager Integration for Container Execution Environment.

Provides integration points for the container execution environment
with the existing agent-manager system in Gadugi.
"""

import logging
import os
import tempfile
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .execution_engine import ContainerExecutionEngine, ExecutionRequest, ExecutionResponse

logger = logging.getLogger(__name__)


class AgentContainerExecutor:
    """
    Container executor for agent-manager integration.
    
    Provides a drop-in replacement for shell execution that uses
    secure containerized execution instead.
    """
    
    def __init__(self, 
                 default_policy: str = "standard",
                 audit_enabled: bool = True):
        """
        Initialize agent container executor.
        
        Args:
            default_policy: Default security policy to use
            audit_enabled: Enable audit logging
        """
        self.default_policy = default_policy
        self.audit_enabled = audit_enabled
        self.execution_engine = ContainerExecutionEngine()
        
        logger.info(f"Agent container executor initialized with policy: {default_policy}")
    
    def execute_script(self, script_path: str, 
                      security_policy: Optional[str] = None,
                      timeout: Optional[int] = None,
                      environment: Optional[Dict[str, str]] = None,
                      user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a script file in a secure container.
        
        Args:
            script_path: Path to script file to execute
            security_policy: Security policy to use (defaults to default_policy)
            timeout: Execution timeout in seconds
            environment: Environment variables
            user_id: User ID for audit logging
            
        Returns:
            Execution result dictionary
        """
        try:
            # Read script content
            script_path_obj = Path(script_path)
            if not script_path_obj.exists():
                raise FileNotFoundError(f"Script file not found: {script_path}")
            
            with open(script_path_obj, 'r') as f:
                script_content = f.read()
            
            # Determine runtime based on file extension
            runtime = self._detect_runtime(script_path_obj)
            
            # Prepare execution request
            if runtime == 'python':
                response = self.execution_engine.execute_python_code(
                    code=script_content,
                    security_policy=security_policy or self.default_policy,
                    timeout=timeout,
                    user_id=user_id
                )
            elif runtime == 'node':
                response = self.execution_engine.execute_node_code(
                    code=script_content,
                    security_policy=security_policy or self.default_policy,
                    timeout=timeout,
                    user_id=user_id
                )
            else:  # Default to shell
                response = self.execution_engine.execute_shell_script(
                    script=script_content,
                    security_policy=security_policy or self.default_policy,
                    timeout=timeout,
                    user_id=user_id
                )
            
            # Convert to agent-manager compatible format
            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"Error executing script {script_path}: {e}")
            return {
                'success': False,
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0.0,
                'error': str(e)
            }
    
    def execute_command(self, command: Union[str, List[str]],
                       security_policy: Optional[str] = None,
                       timeout: Optional[int] = None,
                       environment: Optional[Dict[str, str]] = None,
                       user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a command in a secure container.
        
        Args:
            command: Command to execute (string or list)
            security_policy: Security policy to use
            timeout: Execution timeout in seconds
            environment: Environment variables
            user_id: User ID for audit logging
            
        Returns:
            Execution result dictionary
        """
        try:
            # Convert command to list if string
            if isinstance(command, str):
                cmd_list = ['/bin/sh', '-c', command]
            else:
                cmd_list = command
            
            # Create execution request
            request = ExecutionRequest(
                runtime='shell',
                command=cmd_list,
                environment=environment,
                security_policy=security_policy or self.default_policy,
                timeout=timeout,
                user_id=user_id
            )
            
            # Execute
            response = self.execution_engine.execute(request)
            
            # Convert to agent-manager compatible format
            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            return {
                'success': False,
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0.0,
                'error': str(e)
            }
    
    def execute_python_code(self, code: str,
                           packages: Optional[List[str]] = None,
                           security_policy: Optional[str] = None,
                           timeout: Optional[int] = None,
                           user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute Python code in a secure container.
        
        Args:
            code: Python code to execute
            packages: Python packages to install
            security_policy: Security policy to use
            timeout: Execution timeout in seconds
            user_id: User ID for audit logging
            
        Returns:
            Execution result dictionary
        """
        try:
            response = self.execution_engine.execute_python_code(
                code=code,
                packages=packages,
                security_policy=security_policy or self.default_policy,
                timeout=timeout,
                user_id=user_id
            )
            
            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            return {
                'success': False,
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0.0,
                'error': str(e)
            }
    
    def _detect_runtime(self, script_path: Path) -> str:
        """Detect runtime based on file extension."""
        extension = script_path.suffix.lower()
        
        runtime_map = {
            '.py': 'python',
            '.js': 'node',
            '.mjs': 'node',
            '.ts': 'node',  # TypeScript would need compilation
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell'
        }
        
        return runtime_map.get(extension, 'shell')
    
    def _format_response(self, response: ExecutionResponse) -> Dict[str, Any]:
        """Format execution response for agent-manager compatibility."""
        return {
            'success': response.success,
            'exit_code': response.exit_code,
            'stdout': response.stdout,
            'stderr': response.stderr,
            'execution_time': response.execution_time,
            'request_id': response.request_id,
            'resource_usage': response.resource_usage,
            'security_events': response.security_events,
            'audit_events': response.audit_events,
            'error': response.error_message
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and statistics."""
        return self.execution_engine.get_execution_statistics()
    
    def cleanup(self) -> Dict[str, int]:
        """Clean up resources."""
        return self.execution_engine.cleanup_resources()
    
    def shutdown(self) -> None:
        """Shutdown executor."""
        self.execution_engine.shutdown()


def create_agent_executor(policy: str = "standard") -> AgentContainerExecutor:
    """
    Create an agent container executor with specified policy.
    
    Args:
        policy: Security policy to use
        
    Returns:
        Configured agent container executor
    """
    return AgentContainerExecutor(default_policy=policy)


def replace_shell_execution():
    """
    Replace shell execution with container execution.
    
    This function can be called to monkey-patch subprocess calls
    to use container execution instead.
    """
    import subprocess
    
    # Store original subprocess functions
    original_run = subprocess.run
    original_popen = subprocess.Popen
    
    # Create global executor
    global_executor = create_agent_executor()
    
    def containerized_run(*args, **kwargs):
        """Containerized replacement for subprocess.run."""
        # Extract command
        if args:
            command = args[0]
        else:
            command = kwargs.get('args', [])
        
        # Use container execution
        result = global_executor.execute_command(command)
        
        # Create subprocess.CompletedProcess-like result
        class ContainerResult:
            def __init__(self, result_dict):
                self.returncode = result_dict['exit_code']
                self.stdout = result_dict['stdout']
                self.stderr = result_dict['stderr']
                self.args = command
        
        return ContainerResult(result)
    
    # Replace subprocess functions
    subprocess.run = containerized_run
    
    logger.info("Shell execution replaced with container execution")
    
    # Return cleanup function
    def restore_shell_execution():
        subprocess.run = original_run
        subprocess.Popen = original_popen
        global_executor.shutdown()
        logger.info("Shell execution restored")
    
    return restore_shell_execution


# Example usage functions
def example_python_execution():
    """Example of Python code execution."""
    executor = create_agent_executor("development")
    
    python_code = """
import sys
import os

print("Python version:", sys.version)
print("Environment variables:")
for key, value in sorted(os.environ.items()):
    print(f"  {key}={value}")
    
print("Hello from containerized Python!")
"""
    
    result = executor.execute_python_code(python_code)
    print("Execution result:", result)
    
    executor.shutdown()


def example_shell_execution():
    """Example of shell script execution."""
    executor = create_agent_executor("testing")
    
    shell_script = """
#!/bin/sh
echo "Shell script execution test"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Available commands:"
ls /bin | head -10
echo "Memory info:"
free -h || echo "free command not available"
"""
    
    result = executor.execute_command(shell_script)
    print("Execution result:", result)
    
    executor.shutdown()


if __name__ == "__main__":
    # Run examples
    print("=== Python Execution Example ===")
    example_python_execution()
    
    print("\n=== Shell Execution Example ===")
    example_shell_execution()