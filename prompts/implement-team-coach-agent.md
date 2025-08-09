# Implement Team Coach Agent (#241)

## Overview
Create the Team Coach agent that auto-analyzes completed sessions, identifies improvement opportunities, creates GitHub issues for improvements, and tracks performance trends.

## Requirements

### Location
- Agent directory: `.claude/agents/team-coach/`
- Recipe directory: `.claude/recipes/team-coach/`

### Core Functionality
1. **Session Analysis**
   - Auto-analyze completed development sessions
   - Extract key metrics and patterns
   - Identify bottlenecks and inefficiencies
   - Recognize successful patterns to replicate

2. **Improvement Identification**
   - Detect areas for process improvement
   - Identify recurring issues or problems
   - Suggest workflow optimizations
   - Recommend tooling improvements

3. **GitHub Integration**
   - Automatically create issues for improvements
   - Tag issues appropriately (enhancement, bug, documentation)
   - Link related issues together
   - Track issue resolution progress

4. **Performance Tracking**
   - Monitor performance trends over time
   - Track key metrics (task completion time, error rates, etc.)
   - Generate performance reports
   - Learn from historical data

### Implementation Details

#### Agent Structure
```python
# .claude/agents/team-coach/team_coach.py
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...framework.base_agent import BaseAgent
from ...framework.events import Event, EventType
from ...framework.memory import MemorySystem

class ImprovementType(Enum):
    PROCESS = "process"
    TOOLING = "tooling"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    QUALITY = "quality"

@dataclass
class SessionMetrics:
    session_id: str
    start_time: datetime
    end_time: datetime
    tasks_completed: int
    errors_encountered: int
    test_failures: int
    code_changes: int
    pr_created: bool
    review_comments: int
    performance_score: float

@dataclass
class ImprovementSuggestion:
    type: ImprovementType
    title: str
    description: str
    priority: str  # high, medium, low
    estimated_impact: float  # 0-1 scale
    implementation_steps: List[str]
    related_sessions: List[str] = field(default_factory=list)

@dataclass
class PerformanceTrend:
    metric_name: str
    trend_direction: str  # improving, declining, stable
    current_value: float
    previous_value: float
    change_percentage: float
    time_period: str

class TeamCoach(BaseAgent):
    """Analyzes sessions and provides continuous improvement recommendations"""
    
    def __init__(self):
        super().__init__("TeamCoach")
        self.github_client = self._init_github_client()
        self.metrics_store = self._init_metrics_store()
    
    async def analyze_session(self, session_data: Dict[str, Any]) -> SessionMetrics:
        """Analyze a completed development session"""
        pass
    
    async def identify_improvements(self, metrics: SessionMetrics) -> List[ImprovementSuggestion]:
        """Identify improvement opportunities from session metrics"""
        pass
    
    async def create_improvement_issue(self, suggestion: ImprovementSuggestion) -> str:
        """Create GitHub issue for improvement suggestion"""
        pass
    
    async def track_performance_trends(self) -> List[PerformanceTrend]:
        """Analyze performance trends over time"""
        pass
    
    async def generate_coaching_report(self) -> Dict[str, Any]:
        """Generate comprehensive coaching report"""
        pass
    
    async def learn_from_patterns(self, sessions: List[SessionMetrics]):
        """Learn from successful and unsuccessful patterns"""
        pass
```

#### Recipe Structure
```yaml
# .claude/recipes/team-coach/recipe.yaml
name: team-coach
version: 1.0.0
description: Auto-analyzes sessions and provides continuous improvement coaching

capabilities:
  - session_analysis
  - improvement_identification
  - github_issue_creation
  - performance_tracking
  - pattern_learning
  - coaching_reports

triggers:
  - event: session_completed
    action: analyze_session
  
  - event: pr_merged
    action: track_success_patterns
  
  - event: test_failure
    action: identify_test_improvements
  
  - event: error_logged
    action: analyze_error_patterns

metrics:
  session_metrics:
    - task_completion_rate
    - average_task_time
    - error_frequency
    - test_pass_rate
    - code_quality_score
  
  performance_metrics:
    - velocity_trend
    - quality_trend
    - efficiency_trend
    - learning_curve

improvement_categories:
  process:
    - workflow_optimization
    - task_decomposition
    - parallel_execution
  
  tooling:
    - agent_improvements
    - automation_opportunities
    - integration_enhancements
  
  documentation:
    - missing_documentation
    - outdated_guides
    - unclear_instructions
  
  quality:
    - test_coverage
    - code_review_findings
    - type_safety_issues

github_integration:
  issue_templates:
    improvement:
      title: "[TeamCoach] {title}"
      body: |
        ## Improvement Opportunity
        
        **Type**: {type}
        **Priority**: {priority}
        **Estimated Impact**: {impact}
        
        ## Description
        {description}
        
        ## Implementation Steps
        {steps}
        
        ## Related Sessions
        {sessions}
        
        ---
        *Generated by TeamCoach Agent*
      
      labels:
        - enhancement
        - team-coach
        - continuous-improvement
```

### Quality Requirements
1. **Type Safety**
   - Must pass `uv run pyright` with zero errors
   - Use proper type hints for all functions and variables
   - Handle Optional types correctly

2. **Code Quality**
   - Must be ruff formatted
   - Follow PEP 8 style guidelines
   - Include comprehensive docstrings

3. **Testing**
   - Include unit tests in `tests/test_team_coach.py`
   - Test session analysis logic
   - Test improvement identification
   - Test GitHub issue creation
   - Test performance trend tracking

4. **GitHub Integration**
   - Use GitHub API properly with authentication
   - Handle rate limiting gracefully
   - Create well-formatted issues
   - Link related issues correctly

### Example Usage
```python
coach = TeamCoach()

# Analyze completed session
session_data = {
    "session_id": "sess_20250108_001",
    "duration": 3600,
    "tasks": ["implement-feature-x", "fix-bug-y"],
    "errors": [...],
    "test_results": {...}
}

metrics = await coach.analyze_session(session_data)

# Identify improvements
improvements = await coach.identify_improvements(metrics)

# Create GitHub issues for high-priority improvements
for improvement in improvements:
    if improvement.priority == "high":
        issue_url = await coach.create_improvement_issue(improvement)
        print(f"Created issue: {issue_url}")

# Track performance trends
trends = await coach.track_performance_trends()
for trend in trends:
    if trend.trend_direction == "declining":
        print(f"Alert: {trend.metric_name} is declining by {trend.change_percentage}%")

# Generate coaching report
report = await coach.generate_coaching_report()
```

### Testing Requirements
Create comprehensive tests that verify:
- Correct session analysis and metric extraction
- Accurate improvement identification
- Proper GitHub issue creation
- Performance trend calculation accuracy
- Pattern learning functionality
- Integration with BaseAgent framework
- Event handling capabilities

### Neo4j Integration
Store and query:
- Session metrics as nodes
- Improvement patterns as relationships
- Performance trends over time
- Success/failure patterns
- Team learning history

## Success Criteria
- ✅ Agent inherits from BaseAgent framework
- ✅ Passes pyright with zero errors
- ✅ Comprehensive test coverage
- ✅ GitHub API integration working
- ✅ Neo4j integration for pattern storage
- ✅ Event Router integration
- ✅ Recipe properly configured
- ✅ Documentation complete
- ✅ Auto-analysis triggers working
- ✅ Issues created with proper formatting