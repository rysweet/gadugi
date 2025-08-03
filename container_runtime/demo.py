#!/usr/bin/env python3
"""
Container Execution Environment Demo

Demonstrates the capabilities of the Gadugi Container Execution Environment
with various security policies and execution scenarios.
"""

import sys
import time
import logging
from pathlib import Path

# Add the container runtime to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from container_runtime.execution_engine import ContainerExecutionEngine
from container_runtime.agent_integration import AgentContainerExecutor


def setup_logging():
    """Setup logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def demo_python_execution():
    """Demonstrate Python code execution."""
    print("=== Python Code Execution Demo ===")
    
    try:
        engine = ContainerExecutionEngine()
        
        python_code = """
import sys
import os
import platform

print("Python Execution Environment:")
print(f"  Python version: {sys.version}")
print(f"  Platform: {platform.platform()}")
print(f"  Current user: {os.getenv('USER', 'unknown')}")
print(f"  Working directory: {os.getcwd()}")
print(f"  Available disk space: {os.statvfs('.').f_bavail * os.statvfs('.').f_frsize / (1024*1024):.1f} MB")

# Test some calculations
import math
result = sum(math.sqrt(i) for i in range(1000))
print(f"  Calculation result: {result:.2f}")

print("\\nEnvironment variables:")
for key in sorted(os.environ.keys()):
    print(f"  {key}={os.environ[key]}")
"""
        
        print("Executing Python code with 'standard' security policy...")
        response = engine.execute_python_code(
            code=python_code,
            security_policy="standard",
            timeout=60
        )
        
        print(f"Exit code: {response.exit_code}")
        print(f"Execution time: {response.execution_time:.2f} seconds")
        print(f"Success: {response.success}")
        
        if response.stdout:
            print("Output:")
            print(response.stdout)
        
        if response.stderr:
            print("Errors:")
            print(response.stderr)
        
        print(f"Resource usage: {response.resource_usage}")
        
        engine.shutdown()
        
    except Exception as e:
        print(f"Error: {e}")


def demo_security_policies():
    """Demonstrate different security policies."""
    print("\n=== Security Policy Demo ===")
    
    policies_to_test = ["minimal", "standard", "hardened"]
    test_code = """
import os
import sys

print(f"Security Policy Test - User: {os.getenv('USER', 'unknown')}")
print(f"Available commands in /bin: {len(os.listdir('/bin')) if os.path.exists('/bin') else 'N/A'}")
print(f"Read-only filesystem test:")

try:
    with open('/tmp/test_write.txt', 'w') as f:
        f.write('test')
    print("  /tmp write: SUCCESS")
    os.remove('/tmp/test_write.txt')
except:
    print("  /tmp write: FAILED")

try:
    with open('/test_root_write.txt', 'w') as f:
        f.write('test')
    print("  Root write: SUCCESS (SECURITY ISSUE!)")
except:
    print("  Root write: BLOCKED (Good!)")
"""
    
    try:
        engine = ContainerExecutionEngine()
        
        for policy in policies_to_test:
            print(f"\n--- Testing '{policy}' policy ---")
            
            response = engine.execute_python_code(
                code=test_code,
                security_policy=policy,
                timeout=30
            )
            
            print(f"Exit code: {response.exit_code}")
            print(f"Execution time: {response.execution_time:.2f}s")
            
            if response.stdout:
                # Print only the first few lines to keep output manageable
                lines = response.stdout.split('\n')[:10]
                print("Output (first 10 lines):")
                for line in lines:
                    print(f"  {line}")
        
        engine.shutdown()
        
    except Exception as e:
        print(f"Error: {e}")


def demo_shell_execution():
    """Demonstrate shell script execution."""
    print("\n=== Shell Script Execution Demo ===")
    
    try:
        executor = AgentContainerExecutor(default_policy="standard")
        
        shell_script = """
#!/bin/sh
echo "Shell Script Execution Demo"
echo "=========================="
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "System info:"
echo "  Hostname: $(hostname)"
echo "  Uptime: $(uptime)"
echo "Available commands in /bin:"
ls /bin | head -10 | while read cmd; do echo "  $cmd"; done
echo "Memory info:"
free -h 2>/dev/null || echo "  free command not available"
echo "Disk usage:"
df -h . 2>/dev/null || echo "  df command not available"

# Test some basic commands
echo "Testing basic commands:"
echo "  Date: $(date)"
echo "  Echo test: $(echo 'Hello from container!')"

# Try to access restricted areas
echo "Security tests:"
echo -n "  Can access /etc/passwd: "
if [ -r /etc/passwd ]; then echo "YES"; else echo "NO"; fi
echo -n "  Can write to /tmp: "
if touch /tmp/test_file 2>/dev/null; then echo "YES"; rm -f /tmp/test_file; else echo "NO"; fi
echo -n "  Can write to root: "
if touch /test_file 2>/dev/null; then echo "YES (SECURITY ISSUE!)"; rm -f /test_file; else echo "NO (Good!)"; fi
"""
        
        print("Executing shell script...")
        result = executor.execute_shell_script(
            script=shell_script,
            security_policy="standard",
            timeout=60
        )
        
        print(f"Exit code: {result['exit_code']}")
        print(f"Execution time: {result['execution_time']:.2f} seconds")
        print(f"Success: {result['success']}")
        
        if result['stdout']:
            print("Output:")
            print(result['stdout'])
        
        if result['stderr']:
            print("Errors:")
            print(result['stderr'])
        
        executor.shutdown()
        
    except Exception as e:
        print(f"Error: {e}")


def demo_node_execution():
    """Demonstrate Node.js code execution."""
    print("\n=== Node.js Code Execution Demo ===")
    
    try:
        engine = ContainerExecutionEngine()
        
        node_code = """
console.log("Node.js Execution Environment:");
console.log("  Node version:", process.version);
console.log("  Platform:", process.platform);
console.log("  Architecture:", process.arch);
console.log("  Current directory:", process.cwd());
console.log("  Process ID:", process.pid);
console.log("  Memory usage:", process.memoryUsage());

// Test some calculations
const start = Date.now();
let sum = 0;
for (let i = 0; i < 100000; i++) {
    sum += Math.sqrt(i);
}
const duration = Date.now() - start;
console.log(`  Calculation result: ${sum.toFixed(2)} (took ${duration}ms)`);

// Environment variables
console.log("\\nEnvironment variables:");
Object.keys(process.env).sort().forEach(key => {
    console.log(`  ${key}=${process.env[key]}`);
});

// Test filesystem access
const fs = require('fs');
console.log("\\nFilesystem tests:");
try {
    fs.writeFileSync('/tmp/test.txt', 'Hello from Node.js!');
    const content = fs.readFileSync('/tmp/test.txt', 'utf8');
    console.log("  /tmp write/read: SUCCESS -", content);
    fs.unlinkSync('/tmp/test.txt');
} catch (error) {
    console.log("  /tmp write/read: FAILED -", error.message);
}

try {
    fs.writeFileSync('/test_root.txt', 'This should fail');
    console.log("  Root write: SUCCESS (SECURITY ISSUE!)");
} catch (error) {
    console.log("  Root write: BLOCKED (Good!) -", error.message);
}
"""
        
        print("Executing Node.js code...")
        response = engine.execute_node_code(
            code=node_code,
            security_policy="standard",
            timeout=60
        )
        
        print(f"Exit code: {response.exit_code}")
        print(f"Execution time: {response.execution_time:.2f} seconds")
        print(f"Success: {response.success}")
        
        if response.stdout:
            print("Output:")
            print(response.stdout)
        
        if response.stderr:
            print("Errors:")
            print(response.stderr)
        
        engine.shutdown()
        
    except Exception as e:
        print(f"Error: {e}")


def demo_system_status():
    """Demonstrate system status and monitoring."""
    print("\n=== System Status and Monitoring Demo ===")
    
    try:
        engine = ContainerExecutionEngine()
        
        # Get system statistics
        stats = engine.get_execution_statistics()
        
        print("System Status:")
        print(f"  Active executions: {stats['active_executions']}")
        print(f"  Available policies: {stats['available_policies']}")
        
        if 'system_usage' in stats:
            system = stats['system_usage']
            print(f"  System CPU: {system.get('cpu_percent', 'N/A')}%")
            print(f"  System memory: {system.get('memory_percent', 'N/A')}%")
            print(f"  Active containers: {system.get('active_containers', 'N/A')}")
            print(f"  Max containers: {system.get('max_containers', 'N/A')}")
        
        if 'security_summary' in stats:
            security = stats['security_summary']
            print(f"  Total images: {security.get('total_images', 'N/A')}")
            print(f"  Scanned images: {security.get('scanned_images', 'N/A')}")
            print(f"  Scanner available: {security.get('scanner_available', 'N/A')}")
        
        # Test resource cleanup
        print("\nTesting resource cleanup...")
        cleanup_stats = engine.cleanup_resources()
        print(f"Cleanup results: {cleanup_stats}")
        
        engine.shutdown()
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all demos."""
    print("Gadugi Container Execution Environment Demo")
    print("=" * 50)
    
    setup_logging()
    
    # Check if Docker is available
    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("✓ Docker is available and accessible")
    except Exception as e:
        print(f"✗ Docker not available: {e}")
        print("This demo requires Docker to be installed and running.")
        print("Please install Docker and ensure it's accessible.")
        return 1
    
    try:
        # Run demos in sequence
        demo_python_execution()
        demo_security_policies()
        demo_shell_execution()
        demo_node_execution()
        demo_system_status()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nKey features demonstrated:")
        print("✓ Secure Python code execution")
        print("✓ Multiple security policy levels")
        print("✓ Shell script execution with isolation")
        print("✓ Node.js code execution")
        print("✓ System monitoring and resource management")
        print("✓ Comprehensive audit logging")
        print("✓ Resource cleanup and management")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        return 1
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())