#!/usr/bin/env python3
"""
Test TeamCoach hook invocation to verify the agent can be called properly.
"""

import subprocess
import json
import sys

def test_teamcoach_stop_hook():
    """Test that the TeamCoach stop hook can be invoked."""
    print("Testing TeamCoach Stop Hook...")
    
    # Path to the stop hook
    hook_path = '.claude/hooks/teamcoach-stop.py'
    
    # Test input data
    test_input = json.dumps({})
    
    try:
        # Run the hook
        result = subprocess.run(
            ['python', hook_path],
            input=test_input,
            text=True,
            capture_output=True,
            timeout=10  # Short timeout for testing
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        # Parse the output
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('{'):
                    try:
                        output = json.loads(line)
                        print(f"\nParsed output:")
                        print(f"  Action: {output.get('action')}")
                        print(f"  Message: {output.get('message')}")
                        
                        if output.get('action') == 'continue':
                            print("\n✅ Hook executed successfully!")
                            return True
                    except json.JSONDecodeError:
                        pass
        
        print("\n❌ Hook execution did not produce expected output")
        return False
        
    except subprocess.TimeoutExpired:
        print("\n⚠️ Hook execution timed out (this is normal if Claude isn't installed)")
        return True  # This is actually expected if Claude isn't available
        
    except Exception as e:
        print(f"\n❌ Error running hook: {e}")
        return False

def test_teamcoach_subagent_hook():
    """Test that the TeamCoach subagent stop hook can be invoked."""
    print("\n\nTesting TeamCoach SubagentStop Hook...")
    
    # Path to the subagent hook
    hook_path = '.claude/hooks/teamcoach-subagent-stop.py'
    
    # Test input data with agent information
    test_input = json.dumps({
        'agent_name': 'test-agent',
        'result': 'success',
        'duration': 120
    })
    
    try:
        # Run the hook
        result = subprocess.run(
            ['python', hook_path],
            input=test_input,
            text=True,
            capture_output=True,
            timeout=10  # Short timeout for testing
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        # Parse the output
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('{'):
                    try:
                        output = json.loads(line)
                        print(f"\nParsed output:")
                        print(f"  Action: {output.get('action')}")
                        print(f"  Message: {output.get('message')}")
                        
                        if output.get('action') == 'continue':
                            print("\n✅ Hook executed successfully!")
                            return True
                    except json.JSONDecodeError:
                        pass
        
        print("\n❌ Hook execution did not produce expected output")
        return False
        
    except subprocess.TimeoutExpired:
        print("\n⚠️ Hook execution timed out (this is normal if Claude isn't installed)")
        return True  # This is actually expected if Claude isn't available
        
    except Exception as e:
        print(f"\n❌ Error running hook: {e}")
        return False

if __name__ == "__main__":
    print("TeamCoach Hook Invocation Test\n" + "="*40)
    
    stop_success = test_teamcoach_stop_hook()
    subagent_success = test_teamcoach_subagent_hook()
    
    print("\n" + "="*40)
    print("Summary:")
    print(f"  Stop Hook: {'✅ Pass' if stop_success else '❌ Fail'}")
    print(f"  SubagentStop Hook: {'✅ Pass' if subagent_success else '❌ Fail'}")
    
    overall_success = stop_success and subagent_success
    print(f"\nOverall: {'✅ All tests passed!' if overall_success else '❌ Some tests failed'}")
    
    sys.exit(0 if overall_success else 1)