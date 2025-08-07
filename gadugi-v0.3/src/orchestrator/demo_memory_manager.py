#!/usr/bin/env python3
"""
Demo script for Memory Manager Engine

Shows the memory manager capabilities including:
- Parsing Memory.md content
- Updating memory with new items
- Pruning old content
- GitHub synchronization (mocked)
- Status reporting
"""

import json
from memory_manager_engine import run_memory_manager


def demo_memory_manager():
    """Demonstrate memory manager capabilities"""
    
    print("🧠 Memory Manager Engine Demo")
    print("=" * 50)
    
    # Sample memory content
    sample_memory = """# AI Assistant Memory

## Active Goals
- ✅ Complete memory manager implementation (PR #177)
- 🔄 Implement remaining 7 agents for v0.3
- High priority: Add comprehensive testing

## Current Context  
- Branch: feature/v0.3-memory-manager
- Working on memory management capabilities
- System has 7/15 agents complete

## Recent Accomplishments
- ✅ Created memory manager agent structure
- ✅ Implemented core memory parsing logic
- ✅ Added GitHub Issues synchronization
- ✅ Built comprehensive test suite (23 tests)

## Important Context
- Memory manager handles bidirectional GitHub sync
- Supports automatic pruning of outdated content
- Maintains structured memory format across sessions
- Integrates with existing agent orchestration system

## Reflections
- Memory parsing works well with existing Memory.md format
- GitHub integration provides good visibility into AI progress
- Pruning logic helps keep memory files manageable
- Test coverage ensures reliability across operations
"""
    
    print("\n1. 📊 Getting Memory Status")
    print("-" * 30)
    
    status_request = {
        'action': 'status',
        'memory_content': sample_memory
    }
    
    status_result = run_memory_manager(status_request)
    print(f"✅ Memory analysis complete:")
    stats = status_result['statistics']
    print(f"   • Total sections: {stats['total_sections']}")
    print(f"   • Total items: {stats['total_items']}")
    print(f"   • GitHub CLI available: {stats['github_cli_available']}")
    print(f"   • Items by type: {stats['items_by_type']}")
    print(f"   • Items by priority: {stats['items_by_priority']}")
    
    print("\n2. 🔄 Adding New Memory Items")
    print("-" * 30)
    
    update_request = {
        'action': 'update',
        'memory_content': sample_memory,
        'updates': [
            {
                'type': 'accomplishment',
                'content': '✅ Successfully implemented memory manager engine with 23 passing tests',
                'priority': 'high',
                'metadata': {
                    'component': 'memory-manager',
                    'test_count': 23,
                    'branch': 'feature/v0.3-memory-manager'
                }
            },
            {
                'type': 'goal',
                'content': '🔄 Create PR for memory manager and merge to main branch',
                'priority': 'high',
                'metadata': {
                    'milestone': 'v0.3',
                    'estimated_effort': 'low'
                }
            },
            {
                'type': 'context',
                'content': 'Memory manager demonstrates sophisticated parsing and GitHub integration',
                'priority': 'medium',
                'metadata': {
                    'category': 'architecture'
                }
            }
        ]
    }
    
    update_result = run_memory_manager(update_request)
    print(f"✅ Memory updated successfully:")
    print(f"   • Items added: {update_result['statistics']['items_added']}")
    print(f"   • Actions taken: {len(update_result['actions_taken'])}")
    
    # Get updated memory
    updated_memory = update_result['updated_memory']
    
    print("\n3. ✂️ Pruning Old Content")
    print("-" * 30)
    
    prune_request = {
        'action': 'prune',
        'memory_content': updated_memory,
        'prune_options': {
            'days_threshold': 7,
            'preserve_critical': True
        }
    }
    
    prune_result = run_memory_manager(prune_request)
    print(f"✅ Memory pruned successfully:")
    if 'items_removed' in prune_result['statistics']:
        print(f"   • Items removed: {prune_result['statistics']['items_removed']}")
    else:
        print("   • No items were old enough to prune")
    
    print("\n4. 🔗 GitHub Synchronization (Demo)")
    print("-" * 30)
    
    sync_request = {
        'action': 'sync',
        'memory_content': updated_memory,
        'sync_options': {
            'create_issues': True,
            'close_completed': True,
            'update_labels': True
        }
    }
    
    sync_result = run_memory_manager(sync_request)
    print(f"✅ GitHub sync completed:")
    sync_stats = sync_result['statistics']
    print(f"   • Issues created: {sync_stats['issues_created']}")
    print(f"   • Issues updated: {sync_stats['issues_updated']}")
    print(f"   • Issues closed: {sync_stats['issues_closed']}")
    
    if sync_result['actions_taken']:
        print("   • Actions taken:")
        for action in sync_result['actions_taken']:
            if action['action'] == 'created_issue':
                print(f"     - Created issue #{action['issue_number']}: {action['title']}")
            elif action['action'] == 'closed_issue':
                print(f"     - Closed issue #{action['issue_number']}: {action['title']}")
    
    print("\n5. 📄 Final Memory State Preview")
    print("-" * 30)
    
    final_memory = prune_result['updated_memory']
    lines = final_memory.split('\n')
    
    # Show first 25 lines of final memory
    print("Final memory content (first 25 lines):")
    print()
    for i, line in enumerate(lines[:25], 1):
        print(f"{i:2d}: {line}")
    
    if len(lines) > 25:
        print(f"... ({len(lines) - 25} more lines)")
    
    print(f"\n📈 Memory Manager Demo Summary")
    print("=" * 50)
    print("✅ Successfully demonstrated:")
    print("   • Memory content parsing and structure analysis")
    print("   • Dynamic memory updates with new accomplishments and goals")
    print("   • Intelligent content pruning with preservation rules")
    print("   • GitHub Issues synchronization capabilities")
    print("   • Comprehensive status reporting and analytics")
    print()
    print("🎯 Memory Manager is ready for integration with:")
    print("   • Orchestrator agent for workflow coordination")
    print("   • Other agents for progress tracking")
    print("   • GitHub workflow for issue management")
    print("   • Automated memory maintenance processes")
    
    return {
        'status_result': status_result,
        'update_result': update_result, 
        'prune_result': prune_result,
        'sync_result': sync_result,
        'final_memory': final_memory
    }


if __name__ == '__main__':
    try:
        results = demo_memory_manager()
        print(f"\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()