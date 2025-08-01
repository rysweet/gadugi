"""
TeamCoach Phase 3: Conflict Resolver

Detects and resolves conflicts between agents including resource contention,
task overlap, coordination failures, and capability mismatches.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur between agents."""
    RESOURCE_CONTENTION = "resource_contention"
    TASK_OVERLAP = "task_overlap"
    COORDINATION_FAILURE = "coordination_failure"
    CAPABILITY_MISMATCH = "capability_mismatch"
    DEPENDENCY_DEADLOCK = "dependency_deadlock"
    COMMUNICATION_BREAKDOWN = "communication_breakdown"
    PRIORITY_CONFLICT = "priority_conflict"


class ConflictSeverity(Enum):
    """Severity levels for conflicts."""
    CRITICAL = "critical"  # Blocks work
    HIGH = "high"  # Significantly impacts productivity
    MEDIUM = "medium"  # Noticeable impact
    LOW = "low"  # Minor impact


class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts."""
    IMMEDIATE_REALLOCATION = "immediate_reallocation"
    SCHEDULED_ADJUSTMENT = "scheduled_adjustment"
    NEGOTIATION = "negotiation"
    ESCALATION = "escalation"
    AUTOMATION = "automation"
    PROCESS_CHANGE = "process_change"


@dataclass
class AgentConflict:
    """Represents a conflict between agents."""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    agents_involved: List[str]
    description: str
    impact: str
    detected_at: datetime
    evidence: Dict[str, Any]
    resolution_deadline: Optional[datetime] = None


@dataclass
class ConflictResolution:
    """Represents a resolution for a conflict."""
    conflict_id: str
    strategy: ResolutionStrategy
    actions: List[Dict[str, Any]]
    expected_outcome: str
    implementation_steps: List[str]
    timeline: str
    assigned_to: Optional[str] = None
    created_at: datetime = None


@dataclass
class ConflictReport:
    """Comprehensive conflict analysis report."""
    active_conflicts: List[AgentConflict]
    resolved_conflicts: List[Tuple[AgentConflict, ConflictResolution]]
    conflict_patterns: Dict[str, Any]
    prevention_recommendations: List[str]
    generated_at: datetime


class ConflictResolver:
    """
    Detects and resolves conflicts between agents in multi-agent teams.
    
    Features:
    - Real-time conflict detection
    - Intelligent resolution strategies
    - Pattern analysis for prevention
    - Automated conflict resolution
    - Escalation management
    """
    
    def __init__(self):
        """Initialize the conflict resolver."""
        self.active_conflicts: Dict[str, AgentConflict] = {}
        self.resolved_conflicts: List[Tuple[AgentConflict, ConflictResolution]] = []
        self.conflict_patterns: Dict[str, int] = {}
        
        # Resolution thresholds
        self.resolution_timeouts = {
            ConflictSeverity.CRITICAL: 1,  # 1 hour
            ConflictSeverity.HIGH: 4,  # 4 hours
            ConflictSeverity.MEDIUM: 24,  # 1 day
            ConflictSeverity.LOW: 72  # 3 days
        }
    
    def detect_conflicts(self, 
                        agent_states: Dict[str, Dict[str, Any]],
                        team_context: Dict[str, Any]) -> List[AgentConflict]:
        """
        Detect conflicts between agents based on their states and team context.
        
        Args:
            agent_states: Current state information for all agents
            team_context: Team-level context including tasks, resources, etc.
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Check for resource contention
        resource_conflicts = self._detect_resource_contention(agent_states, team_context)
        conflicts.extend(resource_conflicts)
        
        # Check for task overlap
        task_conflicts = self._detect_task_overlap(agent_states, team_context)
        conflicts.extend(task_conflicts)
        
        # Check for coordination failures
        coord_conflicts = self._detect_coordination_failures(agent_states, team_context)
        conflicts.extend(coord_conflicts)
        
        # Check for capability mismatches
        capability_conflicts = self._detect_capability_mismatches(agent_states, team_context)
        conflicts.extend(capability_conflicts)
        
        # Check for dependency deadlocks
        deadlock_conflicts = self._detect_dependency_deadlocks(agent_states, team_context)
        conflicts.extend(deadlock_conflicts)
        
        # Update active conflicts
        for conflict in conflicts:
            self.active_conflicts[conflict.conflict_id] = conflict
            self._update_conflict_patterns(conflict)
        
        return conflicts
    
    def resolve_conflict(self, conflict: AgentConflict) -> ConflictResolution:
        """
        Generate a resolution for a specific conflict.
        
        Args:
            conflict: The conflict to resolve
            
        Returns:
            Resolution strategy and implementation plan
        """
        # Select resolution strategy based on conflict type and severity
        strategy = self._select_resolution_strategy(conflict)
        
        # Generate resolution actions
        actions = self._generate_resolution_actions(conflict, strategy)
        
        # Create implementation steps
        implementation_steps = self._create_implementation_steps(conflict, strategy, actions)
        
        # Determine timeline
        timeline = self._determine_resolution_timeline(conflict)
        
        # Create resolution
        resolution = ConflictResolution(
            conflict_id=conflict.conflict_id,
            strategy=strategy,
            actions=actions,
            expected_outcome=self._describe_expected_outcome(conflict, strategy),
            implementation_steps=implementation_steps,
            timeline=timeline,
            created_at=datetime.utcnow()
        )
        
        return resolution
    
    def implement_resolution(self,
                           conflict: AgentConflict,
                           resolution: ConflictResolution,
                           agent_states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Implement a conflict resolution.
        
        Args:
            conflict: The conflict being resolved
            resolution: The resolution to implement
            agent_states: Current agent states to modify
            
        Returns:
            Implementation result with updated states
        """
        result = {
            'success': False,
            'updated_states': {},
            'messages': [],
            'follow_up_required': False
        }
        
        try:
            # Execute resolution actions
            for action in resolution.actions:
                action_result = self._execute_resolution_action(
                    action, agent_states, conflict
                )
                
                if action_result['success']:
                    result['messages'].append(action_result['message'])
                    # Update agent states if modified
                    if 'state_updates' in action_result:
                        for agent_id, updates in action_result['state_updates'].items():
                            if agent_id not in result['updated_states']:
                                result['updated_states'][agent_id] = {}
                            result['updated_states'][agent_id].update(updates)
                else:
                    result['messages'].append(f"Failed: {action_result['message']}")
                    result['follow_up_required'] = True
            
            # Mark conflict as resolved if all actions succeeded
            if not result['follow_up_required']:
                self._mark_conflict_resolved(conflict, resolution)
                result['success'] = True
            
        except Exception as e:
            logger.error(f"Error implementing resolution: {str(e)}")
            result['messages'].append(f"Implementation error: {str(e)}")
            result['follow_up_required'] = True
        
        return result
    
    def generate_conflict_report(self) -> ConflictReport:
        """
        Generate a comprehensive conflict analysis report.
        
        Returns:
            Detailed conflict report with patterns and recommendations
        """
        # Analyze conflict patterns
        patterns = self._analyze_conflict_patterns()
        
        # Generate prevention recommendations
        recommendations = self._generate_prevention_recommendations(patterns)
        
        # Create report
        report = ConflictReport(
            active_conflicts=list(self.active_conflicts.values()),
            resolved_conflicts=self.resolved_conflicts[-50:],  # Last 50 resolutions
            conflict_patterns=patterns,
            prevention_recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
        
        return report
    
    def _detect_resource_contention(self,
                                  agent_states: Dict[str, Dict[str, Any]],
                                  team_context: Dict[str, Any]) -> List[AgentConflict]:
        """Detect resource contention conflicts."""
        conflicts = []
        
        # Track resource usage
        resource_usage: Dict[str, List[str]] = {}
        
        for agent_id, state in agent_states.items():
            if 'resources' in state:
                for resource in state['resources']:
                    if resource not in resource_usage:
                        resource_usage[resource] = []
                    resource_usage[resource].append(agent_id)
        
        # Find contentions
        for resource, agents in resource_usage.items():
            if len(agents) > 1:
                # Check if resource allows concurrent access
                resource_info = team_context.get('resources', {}).get(resource, {})
                max_concurrent = resource_info.get('max_concurrent', 1)
                
                if len(agents) > max_concurrent:
                    conflict = AgentConflict(
                        conflict_id=f"resource_{resource}_{datetime.utcnow().timestamp()}",
                        conflict_type=ConflictType.RESOURCE_CONTENTION,
                        severity=self._assess_resource_conflict_severity(
                            resource, agents, resource_info
                        ),
                        agents_involved=agents,
                        description=f"Multiple agents competing for resource '{resource}'",
                        impact=f"{len(agents)} agents blocked or slowed by resource contention",
                        detected_at=datetime.utcnow(),
                        evidence={
                            'resource': resource,
                            'competing_agents': agents,
                            'max_concurrent': max_concurrent
                        }
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_task_overlap(self,
                           agent_states: Dict[str, Dict[str, Any]],
                           team_context: Dict[str, Any]) -> List[AgentConflict]:
        """Detect task overlap conflicts."""
        conflicts = []
        
        # Track task assignments
        task_assignments: Dict[str, List[str]] = {}
        
        for agent_id, state in agent_states.items():
            if 'assigned_tasks' in state:
                for task_id in state['assigned_tasks']:
                    if task_id not in task_assignments:
                        task_assignments[task_id] = []
                    task_assignments[task_id].append(agent_id)
        
        # Find overlaps
        for task_id, agents in task_assignments.items():
            if len(agents) > 1:
                task_info = team_context.get('tasks', {}).get(task_id, {})
                
                # Check if task allows collaboration
                if not task_info.get('collaborative', False):
                    conflict = AgentConflict(
                        conflict_id=f"task_{task_id}_{datetime.utcnow().timestamp()}",
                        conflict_type=ConflictType.TASK_OVERLAP,
                        severity=ConflictSeverity.HIGH,
                        agents_involved=agents,
                        description=f"Multiple agents assigned to non-collaborative task '{task_id}'",
                        impact="Duplicated effort and potential conflicts in deliverables",
                        detected_at=datetime.utcnow(),
                        evidence={
                            'task_id': task_id,
                            'assigned_agents': agents,
                            'task_type': task_info.get('type', 'unknown')
                        }
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_coordination_failures(self,
                                    agent_states: Dict[str, Dict[str, Any]],
                                    team_context: Dict[str, Any]) -> List[AgentConflict]:
        """Detect coordination failure conflicts."""
        conflicts = []
        
        # Check for missed handoffs
        for agent_id, state in agent_states.items():
            if 'waiting_for' in state:
                for dependency in state['waiting_for']:
                    provider_id = dependency.get('provider')
                    wait_time = dependency.get('wait_time', 0)
                    
                    # Check if wait time exceeds threshold
                    if wait_time > 3600:  # 1 hour
                        conflict = AgentConflict(
                            conflict_id=f"coord_{agent_id}_{provider_id}_{datetime.utcnow().timestamp()}",
                            conflict_type=ConflictType.COORDINATION_FAILURE,
                            severity=ConflictSeverity.HIGH if wait_time > 7200 else ConflictSeverity.MEDIUM,
                            agents_involved=[agent_id, provider_id],
                            description=f"Agent {agent_id} blocked waiting for {provider_id}",
                            impact=f"Work blocked for {wait_time/3600:.1f} hours",
                            detected_at=datetime.utcnow(),
                            evidence={
                                'waiting_agent': agent_id,
                                'blocking_agent': provider_id,
                                'wait_time': wait_time,
                                'dependency': dependency
                            }
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def _detect_capability_mismatches(self,
                                    agent_states: Dict[str, Dict[str, Any]],
                                    team_context: Dict[str, Any]) -> List[AgentConflict]:
        """Detect capability mismatch conflicts."""
        conflicts = []
        
        for agent_id, state in agent_states.items():
            if 'assigned_tasks' in state and 'capabilities' in state:
                agent_capabilities = set(state['capabilities'])
                
                for task_id in state['assigned_tasks']:
                    task_info = team_context.get('tasks', {}).get(task_id, {})
                    required_capabilities = set(task_info.get('required_capabilities', []))
                    
                    missing_capabilities = required_capabilities - agent_capabilities
                    
                    if missing_capabilities:
                        conflict = AgentConflict(
                            conflict_id=f"capability_{agent_id}_{task_id}_{datetime.utcnow().timestamp()}",
                            conflict_type=ConflictType.CAPABILITY_MISMATCH,
                            severity=ConflictSeverity.HIGH,
                            agents_involved=[agent_id],
                            description=f"Agent {agent_id} lacks capabilities for task {task_id}",
                            impact="Task likely to fail or produce suboptimal results",
                            detected_at=datetime.utcnow(),
                            evidence={
                                'agent_id': agent_id,
                                'task_id': task_id,
                                'missing_capabilities': list(missing_capabilities),
                                'agent_capabilities': list(agent_capabilities)
                            }
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def _detect_dependency_deadlocks(self,
                                   agent_states: Dict[str, Dict[str, Any]],
                                   team_context: Dict[str, Any]) -> List[AgentConflict]:
        """Detect circular dependency deadlocks."""
        conflicts = []
        
        # Build dependency graph
        dependencies: Dict[str, Set[str]] = {}
        
        for agent_id, state in agent_states.items():
            if 'waiting_for' in state:
                dependencies[agent_id] = set()
                for dep in state['waiting_for']:
                    provider = dep.get('provider')
                    if provider:
                        dependencies[agent_id].add(provider)
        
        # Detect cycles using DFS
        def find_cycle(node: str, visited: Set[str], path: List[str]) -> Optional[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            if node in dependencies:
                for neighbor in dependencies[node]:
                    cycle = find_cycle(neighbor, visited, path[:])
                    if cycle:
                        return cycle
            
            return None
        
        visited = set()
        for agent_id in dependencies:
            if agent_id not in visited:
                cycle = find_cycle(agent_id, visited, [])
                if cycle:
                    conflict = AgentConflict(
                        conflict_id=f"deadlock_{'-'.join(cycle)}_{datetime.utcnow().timestamp()}",
                        conflict_type=ConflictType.DEPENDENCY_DEADLOCK,
                        severity=ConflictSeverity.CRITICAL,
                        agents_involved=cycle,
                        description=f"Circular dependency deadlock: {' → '.join(cycle + [cycle[0]])}",
                        impact="All agents in cycle are blocked indefinitely",
                        detected_at=datetime.utcnow(),
                        evidence={
                            'cycle': cycle,
                            'dependencies': {a: list(dependencies.get(a, [])) for a in cycle}
                        }
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _select_resolution_strategy(self, conflict: AgentConflict) -> ResolutionStrategy:
        """Select appropriate resolution strategy based on conflict type and severity."""
        
        # Critical conflicts need immediate action
        if conflict.severity == ConflictSeverity.CRITICAL:
            if conflict.conflict_type == ConflictType.DEPENDENCY_DEADLOCK:
                return ResolutionStrategy.IMMEDIATE_REALLOCATION
            elif conflict.conflict_type == ConflictType.RESOURCE_CONTENTION:
                return ResolutionStrategy.IMMEDIATE_REALLOCATION
            else:
                return ResolutionStrategy.ESCALATION
        
        # Type-specific strategies
        strategy_map = {
            ConflictType.RESOURCE_CONTENTION: ResolutionStrategy.SCHEDULED_ADJUSTMENT,
            ConflictType.TASK_OVERLAP: ResolutionStrategy.IMMEDIATE_REALLOCATION,
            ConflictType.COORDINATION_FAILURE: ResolutionStrategy.NEGOTIATION,
            ConflictType.CAPABILITY_MISMATCH: ResolutionStrategy.IMMEDIATE_REALLOCATION,
            ConflictType.COMMUNICATION_BREAKDOWN: ResolutionStrategy.PROCESS_CHANGE,
            ConflictType.PRIORITY_CONFLICT: ResolutionStrategy.NEGOTIATION
        }
        
        return strategy_map.get(conflict.conflict_type, ResolutionStrategy.ESCALATION)
    
    def _generate_resolution_actions(self,
                                   conflict: AgentConflict,
                                   strategy: ResolutionStrategy) -> List[Dict[str, Any]]:
        """Generate specific actions to resolve the conflict."""
        actions = []
        
        if conflict.conflict_type == ConflictType.RESOURCE_CONTENTION:
            if strategy == ResolutionStrategy.IMMEDIATE_REALLOCATION:
                # Prioritize agents and reassign
                priority_order = self._prioritize_agents(conflict.agents_involved)
                for i, agent_id in enumerate(priority_order[1:], 1):
                    actions.append({
                        'type': 'reassign_resource',
                        'agent_id': agent_id,
                        'action': 'find_alternative',
                        'priority': i
                    })
            elif strategy == ResolutionStrategy.SCHEDULED_ADJUSTMENT:
                # Create time-based schedule
                for i, agent_id in enumerate(conflict.agents_involved):
                    actions.append({
                        'type': 'schedule_resource',
                        'agent_id': agent_id,
                        'time_slot': i,
                        'duration': 'auto'
                    })
        
        elif conflict.conflict_type == ConflictType.TASK_OVERLAP:
            # Reassign task to single agent
            best_agent = self._select_best_agent_for_task(
                conflict.agents_involved,
                conflict.evidence.get('task_id')
            )
            for agent_id in conflict.agents_involved:
                if agent_id != best_agent:
                    actions.append({
                        'type': 'remove_task',
                        'agent_id': agent_id,
                        'task_id': conflict.evidence.get('task_id')
                    })
        
        elif conflict.conflict_type == ConflictType.DEPENDENCY_DEADLOCK:
            # Break the cycle
            cycle = conflict.evidence.get('cycle', [])
            if cycle:
                # Remove one dependency to break cycle
                actions.append({
                    'type': 'break_dependency',
                    'from_agent': cycle[0],
                    'to_agent': cycle[1],
                    'alternative': 'provide_mock_data'
                })
        
        elif conflict.conflict_type == ConflictType.CAPABILITY_MISMATCH:
            # Reassign to capable agent or provide support
            task_id = conflict.evidence.get('task_id')
            agent_id = conflict.agents_involved[0]
            actions.append({
                'type': 'reassign_task',
                'from_agent': agent_id,
                'task_id': task_id,
                'to_agent': 'find_capable_agent'
            })
        
        return actions
    
    def _create_implementation_steps(self,
                                   conflict: AgentConflict,
                                   strategy: ResolutionStrategy,
                                   actions: List[Dict[str, Any]]) -> List[str]:
        """Create detailed implementation steps."""
        steps = []
        
        # Add strategy-specific preparation
        if strategy == ResolutionStrategy.IMMEDIATE_REALLOCATION:
            steps.append("1. Notify all affected agents of immediate changes")
            steps.append("2. Save current state for rollback if needed")
        elif strategy == ResolutionStrategy.NEGOTIATION:
            steps.append("1. Schedule negotiation session with involved agents")
            steps.append("2. Prepare compromise proposals")
        
        # Add action-specific steps
        for i, action in enumerate(actions, len(steps) + 1):
            if action['type'] == 'reassign_resource':
                steps.append(f"{i}. Find alternative resource for agent {action['agent_id']}")
                steps.append(f"{i+1}. Update agent {action['agent_id']} configuration")
            elif action['type'] == 'remove_task':
                steps.append(f"{i}. Remove task {action['task_id']} from agent {action['agent_id']}")
                steps.append(f"{i+1}. Update task assignment records")
        
        # Add verification step
        steps.append(f"{len(steps)+1}. Verify conflict resolution and monitor for recurrence")
        
        return steps
    
    def _determine_resolution_timeline(self, conflict: AgentConflict) -> str:
        """Determine timeline for resolution based on severity."""
        timelines = {
            ConflictSeverity.CRITICAL: "Immediate (within 1 hour)",
            ConflictSeverity.HIGH: "Within 4 hours",
            ConflictSeverity.MEDIUM: "Within 24 hours",
            ConflictSeverity.LOW: "Within 3 days"
        }
        return timelines.get(conflict.severity, "Within 1 week")
    
    def _describe_expected_outcome(self,
                                 conflict: AgentConflict,
                                 strategy: ResolutionStrategy) -> str:
        """Describe the expected outcome of the resolution."""
        if conflict.conflict_type == ConflictType.RESOURCE_CONTENTION:
            return "All agents have access to required resources without contention"
        elif conflict.conflict_type == ConflictType.TASK_OVERLAP:
            return "Task assigned to single most capable agent, no duplication"
        elif conflict.conflict_type == ConflictType.DEPENDENCY_DEADLOCK:
            return "Circular dependency broken, all agents can proceed"
        elif conflict.conflict_type == ConflictType.CAPABILITY_MISMATCH:
            return "Task reassigned to agent with required capabilities"
        else:
            return "Conflict resolved and normal operations restored"
    
    def _execute_resolution_action(self,
                                 action: Dict[str, Any],
                                 agent_states: Dict[str, Dict[str, Any]],
                                 conflict: AgentConflict) -> Dict[str, Any]:
        """Execute a single resolution action."""
        result = {
            'success': False,
            'message': '',
            'state_updates': {}
        }
        
        try:
            if action['type'] == 'reassign_resource':
                agent_id = action['agent_id']
                # Remove resource from agent's state
                if agent_id in agent_states and 'resources' in agent_states[agent_id]:
                    resource = conflict.evidence.get('resource')
                    if resource in agent_states[agent_id]['resources']:
                        agent_states[agent_id]['resources'].remove(resource)
                        result['state_updates'][agent_id] = {
                            'resources': agent_states[agent_id]['resources']
                        }
                        result['success'] = True
                        result['message'] = f"Removed resource {resource} from agent {agent_id}"
            
            elif action['type'] == 'remove_task':
                agent_id = action['agent_id']
                task_id = action['task_id']
                if agent_id in agent_states and 'assigned_tasks' in agent_states[agent_id]:
                    if task_id in agent_states[agent_id]['assigned_tasks']:
                        agent_states[agent_id]['assigned_tasks'].remove(task_id)
                        result['state_updates'][agent_id] = {
                            'assigned_tasks': agent_states[agent_id]['assigned_tasks']
                        }
                        result['success'] = True
                        result['message'] = f"Removed task {task_id} from agent {agent_id}"
            
            elif action['type'] == 'break_dependency':
                from_agent = action['from_agent']
                to_agent = action['to_agent']
                if from_agent in agent_states and 'waiting_for' in agent_states[from_agent]:
                    agent_states[from_agent]['waiting_for'] = [
                        dep for dep in agent_states[from_agent]['waiting_for']
                        if dep.get('provider') != to_agent
                    ]
                    result['state_updates'][from_agent] = {
                        'waiting_for': agent_states[from_agent]['waiting_for']
                    }
                    result['success'] = True
                    result['message'] = f"Broke dependency from {from_agent} to {to_agent}"
            
            else:
                result['message'] = f"Unknown action type: {action['type']}"
            
        except Exception as e:
            result['message'] = f"Error executing action: {str(e)}"
            logger.error(f"Action execution error: {str(e)}")
        
        return result
    
    def _mark_conflict_resolved(self,
                              conflict: AgentConflict,
                              resolution: ConflictResolution):
        """Mark a conflict as resolved."""
        if conflict.conflict_id in self.active_conflicts:
            del self.active_conflicts[conflict.conflict_id]
        
        self.resolved_conflicts.append((conflict, resolution))
        
        # Keep only recent resolved conflicts
        if len(self.resolved_conflicts) > 100:
            self.resolved_conflicts = self.resolved_conflicts[-100:]
    
    def _update_conflict_patterns(self, conflict: AgentConflict):
        """Update conflict pattern tracking."""
        pattern_key = f"{conflict.conflict_type.value}_{conflict.severity.value}"
        self.conflict_patterns[pattern_key] = self.conflict_patterns.get(pattern_key, 0) + 1
    
    def _analyze_conflict_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in conflicts."""
        total_conflicts = sum(self.conflict_patterns.values())
        
        patterns = {
            'total_conflicts': total_conflicts,
            'by_type': {},
            'by_severity': {},
            'most_common': None,
            'trend': 'stable'  # Would calculate actual trend with historical data
        }
        
        # Analyze by type and severity
        for pattern_key, count in self.conflict_patterns.items():
            conflict_type, severity = pattern_key.split('_', 1)
            
            if conflict_type not in patterns['by_type']:
                patterns['by_type'][conflict_type] = 0
            patterns['by_type'][conflict_type] += count
            
            if severity not in patterns['by_severity']:
                patterns['by_severity'][severity] = 0
            patterns['by_severity'][severity] += count
        
        # Find most common
        if self.conflict_patterns:
            most_common_key = max(self.conflict_patterns, key=self.conflict_patterns.get)
            patterns['most_common'] = {
                'pattern': most_common_key,
                'count': self.conflict_patterns[most_common_key],
                'percentage': (self.conflict_patterns[most_common_key] / total_conflicts * 100) if total_conflicts > 0 else 0
            }
        
        return patterns
    
    def _generate_prevention_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations to prevent future conflicts."""
        recommendations = []
        
        # Based on most common conflict types
        if patterns['most_common']:
            conflict_type = patterns['most_common']['pattern'].split('_')[0]
            
            if conflict_type == 'resource_contention':
                recommendations.append("Implement resource pooling and reservation system")
                recommendations.append("Add resource capacity monitoring and alerts")
            elif conflict_type == 'task_overlap':
                recommendations.append("Improve task assignment algorithm to check for duplicates")
                recommendations.append("Implement task ownership verification before assignment")
            elif conflict_type == 'coordination_failure':
                recommendations.append("Establish SLAs for inter-agent dependencies")
                recommendations.append("Implement dependency timeout alerts")
            elif conflict_type == 'capability_mismatch':
                recommendations.append("Enhance capability validation in task assignment")
                recommendations.append("Implement continuous capability assessment")
        
        # Based on severity patterns
        if patterns['by_severity'].get('critical', 0) > 5:
            recommendations.append("Implement proactive conflict detection system")
            recommendations.append("Create emergency response protocols for critical conflicts")
        
        # General recommendations
        recommendations.append("Regular team coordination reviews")
        recommendations.append("Automated conflict pattern monitoring")
        
        return recommendations
    
    def _assess_resource_conflict_severity(self,
                                         resource: str,
                                         agents: List[str],
                                         resource_info: Dict[str, Any]) -> ConflictSeverity:
        """Assess severity of resource contention."""
        if resource_info.get('critical', False):
            return ConflictSeverity.CRITICAL
        elif len(agents) > 3:
            return ConflictSeverity.HIGH
        else:
            return ConflictSeverity.MEDIUM
    
    def _prioritize_agents(self, agent_ids: List[str]) -> List[str]:
        """Prioritize agents for resource allocation."""
        # In real implementation, would use agent performance, task priority, etc.
        # For now, return as-is
        return agent_ids
    
    def _select_best_agent_for_task(self, agent_ids: List[str], task_id: str) -> str:
        """Select the best agent for a specific task."""
        # In real implementation, would analyze capabilities, availability, etc.
        # For now, return first agent
        return agent_ids[0] if agent_ids else None