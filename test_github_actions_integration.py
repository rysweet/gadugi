#!/usr/bin/env python3
"""
Test script for GitHub Actions Agent Integration

This script validates the GitHub Actions workflows and configurations
for Gadugi AI agent integration.
"""

import os
import yaml
import json
import sys
from pathlib import Path

def test_workflow_files():
    """Test that all workflow files are valid YAML"""
    workflows_dir = Path(".github/workflows")
    errors = []
    
    workflow_files = [
        "label-triggered-agent.yml",
        "pr-review-agent.yml", 
        "issue-triage-agent.yml",
        "templates/custom-agent-invocation.yml"
    ]
    
    for workflow_file in workflow_files:
        workflow_path = workflows_dir / workflow_file
        if not workflow_path.exists():
            errors.append(f"❌ Missing workflow file: {workflow_file}")
            continue
            
        try:
            with open(workflow_path, 'r') as f:
                yaml.safe_load(f)
            print(f"✅ Valid YAML: {workflow_file}")
        except yaml.YAMLError as e:
            errors.append(f"❌ YAML error in {workflow_file}: {e}")
    
    return errors

def test_action_file():
    """Test that the reusable action file is valid"""
    action_path = Path(".github/actions/invoke-agent/action.yml")
    errors = []
    
    if not action_path.exists():
        errors.append("❌ Missing action file: invoke-agent/action.yml")
        return errors
        
    try:
        with open(action_path, 'r') as f:
            action_data = yaml.safe_load(f)
            
        # Validate required action structure
        required_fields = ['name', 'description', 'inputs', 'outputs', 'runs']
        for field in required_fields:
            if field not in action_data:
                errors.append(f"❌ Missing required field in action: {field}")
        
        # Validate required inputs
        required_inputs = ['agent', 'scenario', 'github-token', 'target-type']
        if 'inputs' in action_data:
            for input_name in required_inputs:
                if input_name not in action_data['inputs']:
                    errors.append(f"❌ Missing required input: {input_name}")
        
        print("✅ Valid action file: invoke-agent/action.yml")
        
    except yaml.YAMLError as e:
        errors.append(f"❌ YAML error in action file: {e}")
    
    return errors

def test_configuration_files():
    """Test configuration templates"""
    config_files = [
        ".github/workflows/templates/agent-config.yml",
        ".github/workflows/README.md"
    ]
    
    errors = []
    
    for config_file in config_files:
        config_path = Path(config_file)
        if not config_path.exists():
            errors.append(f"❌ Missing configuration file: {config_file}")
            continue
            
        if config_file.endswith('.yml'):
            try:
                with open(config_path, 'r') as f:
                    yaml.safe_load(f)
                print(f"✅ Valid config: {config_file}")
            except yaml.YAMLError as e:
                errors.append(f"❌ YAML error in {config_file}: {e}")
        else:
            print(f"✅ Documentation exists: {config_file}")
    
    return errors

def test_memory_manager_integration():
    """Test memory manager integration"""
    errors = []
    
    memory_files = [
        ".github/memory-manager/simple_memory_cli.py",
        ".github/memory-manager/simple_memory_manager.py",
        ".github/memory-manager/requirements.txt"
    ]
    
    for memory_file in memory_files:
        if not Path(memory_file).exists():
            errors.append(f"❌ Missing memory manager file: {memory_file}")
        else:
            print(f"✅ Memory manager file exists: {memory_file}")
    
    return errors

def test_agent_availability():
    """Test that required agents are available"""
    agents_dir = Path(".claude/agents")
    errors = []
    
    required_agents = [
        "code-reviewer.md",
        "workflow-master.md", 
        "orchestrator-agent.md",
        "prompt-writer.md"
    ]
    
    if not agents_dir.exists():
        errors.append("❌ Missing .claude/agents directory")
        return errors
    
    for agent_file in required_agents:
        agent_path = agents_dir / agent_file
        if not agent_path.exists():
            errors.append(f"❌ Missing agent: {agent_file}")
        else:
            print(f"✅ Agent available: {agent_file}")
    
    return errors

def generate_test_report():
    """Generate a comprehensive test report"""
    print("🤖 GitHub Actions Agent Integration Test Report")
    print("=" * 60)
    
    all_errors = []
    
    print("\n📝 Testing Workflow Files...")
    all_errors.extend(test_workflow_files())
    
    print("\n🎯 Testing Action File...")
    all_errors.extend(test_action_file())
    
    print("\n⚙️  Testing Configuration Files...")
    all_errors.extend(test_configuration_files())
    
    print("\n🧠 Testing Memory Manager Integration...")
    all_errors.extend(test_memory_manager_integration())
    
    print("\n🤖 Testing Agent Availability...")
    all_errors.extend(test_agent_availability())
    
    print("\n" + "=" * 60)
    
    if all_errors:
        print(f"❌ Test Failed: {len(all_errors)} errors found")
        for error in all_errors:
            print(f"   {error}")
        return False
    else:
        print("✅ All Tests Passed!")
        print("\n🎉 GitHub Actions Integration Ready!")
        print("\nNext Steps:")
        print("1. Commit and push the workflows to enable them")
        print("2. Test with a label: 'gh issue edit <number> --add-label ai-agent:code-reviewer'")
        print("3. Create a PR and mark it ready for review")
        print("4. Create a new issue to test triage automation")
        return True

if __name__ == "__main__":
    success = generate_test_report()
    sys.exit(0 if success else 1)