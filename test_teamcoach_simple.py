#!/usr/bin/env python3
"""
Simple test to verify TeamCoach imports work correctly
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_teamcoach_imports():
    """Test that TeamCoach modules can be imported successfully."""
    try:
        # Test basic imports - use absolute imports
        import claude.shared.interfaces
        import claude.shared.state_management
        import claude.shared.task_tracking
        import claude.shared.error_handling
        
        # Test TeamCoach Phase 1 imports
        import claude.agents.teamcoach.phase1.performance_analytics
        import claude.agents.teamcoach.phase1.capability_assessment
        
        # Test TeamCoach Phase 2 imports
        import claude.agents.teamcoach.phase2.task_matcher
        import claude.agents.teamcoach.phase2.team_optimizer
        
        # Test TeamCoach Phase 3 imports  
        import claude.agents.teamcoach.phase3.coaching_engine
        import claude.agents.teamcoach.phase3.conflict_resolver
        import claude.agents.teamcoach.phase3.workflow_optimizer
        import claude.agents.teamcoach.phase3.strategic_planner
        
        print("✅ All TeamCoach imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    success = test_teamcoach_imports()
    sys.exit(0 if success else 1)