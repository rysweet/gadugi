"""
Task Pattern Recognition System
Advanced pattern recognition and matching for the Enhanced Task Decomposition Analyzer

This module provides sophisticated pattern recognition capabilities including:
- Historical pattern analysis
- Semantic similarity matching
- Performance pattern prediction
- Optimization pattern identification
"""

import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import numpy as np
from enum import Enum


class PatternType(Enum):
    """Types of patterns that can be recognized"""

    IMPLEMENTATION = "implementation"
    OPTIMIZATION = "optimization"
    TESTING = "testing"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    ARCHITECTURAL = "architectural"
    PERFORMANCE = "performance"


class ConfidenceLevel(Enum):
    """Confidence levels for pattern recognition"""

    VERY_HIGH = 0.9
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    VERY_LOW = 0.2


@dataclass
class Pattern:
    """Represents a recognized task pattern"""

    pattern_id: str
    pattern_type: PatternType
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)

    # Pattern characteristics
    complexity_multiplier: float = 1.0
    time_multiplier: float = 1.0
    risk_level: float = 0.5
    parallelization_potential: float = 0.5

    # Optimization suggestions
    recommended_approach: str = ""
    optimization_strategies: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, float] = field(default_factory=dict)

    # Historical data
    usage_count: int = 0
    success_rate: float = 0.8
    average_completion_time: float = 60.0
    last_used: Optional[datetime] = None


@dataclass
class PatternMatch:
    """Represents a pattern match result"""

    pattern: Pattern
    confidence: float
    matching_indicators: List[str] = field(default_factory=list)
    context_relevance: float = 0.0
    historical_relevance: float = 0.0
    semantic_similarity: float = 0.0

    # Match details
    matched_keywords: List[str] = field(default_factory=list)
    matched_indicators: List[str] = field(default_factory=list)
    anti_pattern_violations: List[str] = field(default_factory=list)

    # Recommendations
    suggested_modifications: List[str] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)


class TaskPatternRecognitionSystem:
    """
    Advanced task pattern recognition system for intelligent task analysis.

    This system uses multiple recognition techniques:
    1. Keyword-based pattern matching
    2. Semantic similarity analysis
    3. Historical pattern analysis
    4. Context-aware pattern recognition
    5. Performance pattern prediction
    """

    def __init__(self):
        self.patterns = self._initialize_pattern_library()
        self.semantic_vectors = self._initialize_semantic_vectors()
        self.historical_data = self._initialize_historical_data()
        self.context_analyzer = ContextAnalyzer()
        self.performance_predictor = PerformancePatternPredictor()

    def _initialize_pattern_library(self) -> Dict[str, Pattern]:
        """Initialize comprehensive pattern library"""
        patterns = {}

        # Implementation Patterns
        patterns["mvc_implementation"] = Pattern(
            pattern_id="mvc_implementation",
            pattern_type=PatternType.IMPLEMENTATION,
            name="MVC Architecture Implementation",
            description="Model-View-Controller architectural pattern implementation",
            keywords=["mvc", "model", "view", "controller", "architecture"],
            indicators=[
                "separate concerns",
                "layered architecture",
                "component isolation",
            ],
            complexity_multiplier=1.4,
            time_multiplier=1.3,
            parallelization_potential=0.8,
            recommended_approach="layer_by_layer_implementation",
            optimization_strategies=[
                "parallel_layer_development",
                "interface_first_design",
            ],
            resource_requirements={"cpu": 2.0, "memory": 4.0, "time_hours": 8},
        )

        patterns["api_first_design"] = Pattern(
            pattern_id="api_first_design",
            pattern_type=PatternType.IMPLEMENTATION,
            name="API-First Design Pattern",
            description="Design API interface before implementation",
            keywords=["api", "interface", "design", "contract", "specification"],
            indicators=["api design", "interface definition", "contract first"],
            complexity_multiplier=1.2,
            time_multiplier=1.1,
            parallelization_potential=0.9,
            recommended_approach="contract_driven_development",
            optimization_strategies=[
                "parallel_client_server_development",
                "mock_driven_testing",
            ],
            resource_requirements={"cpu": 1.5, "memory": 2.0, "time_hours": 6},
        )

        patterns["microservice_decomposition"] = Pattern(
            pattern_id="microservice_decomposition",
            pattern_type=PatternType.ARCHITECTURAL,
            name="Microservice Decomposition Pattern",
            description="Break monolith into microservices",
            keywords=["microservice", "decomposition", "service", "distributed"],
            indicators=[
                "service boundaries",
                "domain separation",
                "independent deployment",
            ],
            complexity_multiplier=2.0,
            time_multiplier=1.8,
            risk_level=0.7,
            parallelization_potential=0.9,
            recommended_approach="domain_driven_decomposition",
            optimization_strategies=[
                "service_boundary_analysis",
                "data_consistency_planning",
            ],
            resource_requirements={"cpu": 4.0, "memory": 8.0, "time_hours": 20},
        )

        # Testing Patterns
        patterns["test_driven_development"] = Pattern(
            pattern_id="test_driven_development",
            pattern_type=PatternType.TESTING,
            name="Test-Driven Development",
            description="Write tests before implementation",
            keywords=["tdd", "test driven", "test first", "red green refactor"],
            indicators=["test first", "behavior specification", "fail fast"],
            complexity_multiplier=1.2,
            time_multiplier=1.4,
            parallelization_potential=0.7,
            recommended_approach="red_green_refactor_cycle",
            optimization_strategies=[
                "parallel_test_implementation",
                "mock_driven_design",
            ],
            resource_requirements={"cpu": 1.8, "memory": 3.0, "time_hours": 10},
        )

        patterns["behavior_driven_development"] = Pattern(
            pattern_id="behavior_driven_development",
            pattern_type=PatternType.TESTING,
            name="Behavior-Driven Development",
            description="Define behavior through examples and scenarios",
            keywords=["bdd", "behavior", "scenario", "given when then", "cucumber"],
            indicators=[
                "scenario driven",
                "stakeholder collaboration",
                "living documentation",
            ],
            complexity_multiplier=1.3,
            time_multiplier=1.5,
            parallelization_potential=0.6,
            recommended_approach="scenario_driven_development",
            optimization_strategies=[
                "stakeholder_collaboration",
                "living_documentation",
            ],
            resource_requirements={"cpu": 2.0, "memory": 3.5, "time_hours": 12},
        )

        # Performance Patterns
        patterns["caching_optimization"] = Pattern(
            pattern_id="caching_optimization",
            pattern_type=PatternType.PERFORMANCE,
            name="Caching Optimization Pattern",
            description="Implement caching for performance improvement",
            keywords=["cache", "caching", "performance", "optimization", "speed"],
            indicators=[
                "performance improvement",
                "data access optimization",
                "response time",
            ],
            complexity_multiplier=1.1,
            time_multiplier=1.0,
            parallelization_potential=0.8,
            recommended_approach="layered_caching_strategy",
            optimization_strategies=["cache_hierarchy", "invalidation_strategy"],
            resource_requirements={"cpu": 1.2, "memory": 2.5, "time_hours": 4},
        )

        patterns["database_optimization"] = Pattern(
            pattern_id="database_optimization",
            pattern_type=PatternType.PERFORMANCE,
            name="Database Optimization Pattern",
            description="Optimize database queries and schema",
            keywords=["database", "query", "optimization", "index", "performance"],
            indicators=["query optimization", "index design", "schema optimization"],
            complexity_multiplier=1.5,
            time_multiplier=1.3,
            risk_level=0.6,
            parallelization_potential=0.5,
            recommended_approach="incremental_optimization",
            optimization_strategies=[
                "query_analysis",
                "index_optimization",
                "schema_review",
            ],
            resource_requirements={"cpu": 2.5, "memory": 4.0, "time_hours": 8},
        )

        # Integration Patterns
        patterns["event_driven_architecture"] = Pattern(
            pattern_id="event_driven_architecture",
            pattern_type=PatternType.INTEGRATION,
            name="Event-Driven Architecture",
            description="Use events for system integration",
            keywords=["event", "driven", "messaging", "pub sub", "event sourcing"],
            indicators=["event sourcing", "publish subscribe", "loose coupling"],
            complexity_multiplier=1.6,
            time_multiplier=1.4,
            parallelization_potential=0.9,
            recommended_approach="event_first_design",
            optimization_strategies=["event_schema_design", "message_ordering"],
            resource_requirements={"cpu": 3.0, "memory": 5.0, "time_hours": 15},
        )

        patterns["circuit_breaker"] = Pattern(
            pattern_id="circuit_breaker",
            pattern_type=PatternType.INTEGRATION,
            name="Circuit Breaker Pattern",
            description="Prevent cascading failures in distributed systems",
            keywords=["circuit breaker", "failure", "resilience", "fault tolerance"],
            indicators=["fault tolerance", "failure isolation", "resilience"],
            complexity_multiplier=1.3,
            time_multiplier=1.2,
            parallelization_potential=0.7,
            recommended_approach="graduated_circuit_breaking",
            optimization_strategies=["failure_detection", "recovery_strategies"],
            resource_requirements={"cpu": 1.5, "memory": 2.0, "time_hours": 6},
        )

        # Deployment Patterns
        patterns["blue_green_deployment"] = Pattern(
            pattern_id="blue_green_deployment",
            pattern_type=PatternType.DEPLOYMENT,
            name="Blue-Green Deployment",
            description="Zero-downtime deployment strategy",
            keywords=["blue green", "deployment", "zero downtime", "rollback"],
            indicators=["zero downtime", "instant rollback", "production safety"],
            complexity_multiplier=1.4,
            time_multiplier=1.2,
            parallelization_potential=0.6,
            recommended_approach="environment_parity",
            optimization_strategies=["automated_switching", "health_checks"],
            resource_requirements={"cpu": 2.0, "memory": 4.0, "time_hours": 10},
        )

        patterns["canary_deployment"] = Pattern(
            pattern_id="canary_deployment",
            pattern_type=PatternType.DEPLOYMENT,
            name="Canary Deployment",
            description="Gradual rollout with monitoring",
            keywords=["canary", "gradual", "rollout", "monitoring", "progressive"],
            indicators=["gradual rollout", "risk mitigation", "monitoring driven"],
            complexity_multiplier=1.5,
            time_multiplier=1.3,
            parallelization_potential=0.5,
            recommended_approach="metrics_driven_rollout",
            optimization_strategies=["automated_rollback", "metric_monitoring"],
            resource_requirements={"cpu": 2.5, "memory": 3.5, "time_hours": 12},
        )

        return patterns

    def _initialize_semantic_vectors(self) -> Dict[str, np.ndarray]:
        """Initialize semantic word vectors for similarity analysis"""
        # In a real implementation, this would load pre-trained word embeddings
        # For now, we'll use a simplified approach with keyword-based vectors
        vectors = {}

        # Common technical terms and their simplified vector representations
        technical_terms = [
            "api",
            "database",
            "performance",
            "security",
            "testing",
            "deployment",
            "architecture",
            "optimization",
            "integration",
            "microservice",
            "cache",
            "event",
            "pattern",
            "design",
            "implementation",
            "framework",
        ]

        # Generate simple vectors (in reality, these would be learned embeddings)
        for i, term in enumerate(technical_terms):
            vector = np.zeros(len(technical_terms))
            vector[i] = 1.0
            # Add some noise to make vectors more realistic
            noise = np.random.normal(0, 0.1, len(technical_terms))
            vector += noise
            vectors[term] = vector / np.linalg.norm(vector)  # Normalize

        return vectors

    def _initialize_historical_data(self) -> Dict[str, Any]:
        """Initialize historical pattern usage data"""
        return {
            "pattern_usage": defaultdict(int),
            "pattern_success_rates": defaultdict(float),
            "pattern_completion_times": defaultdict(list),
            "co_occurrence_patterns": defaultdict(lambda: defaultdict(int)),
            "context_associations": defaultdict(lambda: defaultdict(float)),
        }

    def recognize_patterns(
        self,
        task_description: str,
        task_context: Dict[str, Any] = None,
        historical_context: List[str] = None,
    ) -> List[PatternMatch]:
        """
        Recognize patterns in a task description using multiple recognition techniques.

        Args:
            task_description: Text description of the task
            task_context: Additional context about the task
            historical_context: Historical similar tasks

        Returns:
            List of PatternMatch objects sorted by confidence
        """
        task_context = task_context or {}
        historical_context = historical_context or []

        pattern_matches = []

        for _pattern_id, pattern in self.patterns.items():
            match = self._evaluate_pattern_match(
                pattern, task_description, task_context, historical_context
            )

            if match.confidence > 0.2:  # Minimum confidence threshold
                pattern_matches.append(match)

        # Sort by confidence (highest first)
        pattern_matches.sort(key=lambda x: x.confidence, reverse=True)

        # Apply post-processing filters
        pattern_matches = self._post_process_matches(pattern_matches, task_description)

        return pattern_matches

    def _evaluate_pattern_match(
        self,
        pattern: Pattern,
        task_description: str,
        task_context: Dict[str, Any],
        historical_context: List[str],
    ) -> PatternMatch:
        """Evaluate how well a pattern matches the given task"""

        # 1. Keyword-based matching
        keyword_score = self._calculate_keyword_score(pattern, task_description)

        # 2. Indicator-based matching
        indicator_score = self._calculate_indicator_score(pattern, task_description)

        # 3. Semantic similarity
        semantic_score = self._calculate_semantic_similarity(pattern, task_description)

        # 4. Context relevance
        context_score = self._calculate_context_relevance(pattern, task_context)

        # 5. Historical relevance
        historical_score = self._calculate_historical_relevance(
            pattern, historical_context
        )

        # 6. Anti-pattern violations
        anti_pattern_penalty = self._calculate_anti_pattern_penalty(
            pattern, task_description
        )

        # Combine scores with weights
        total_confidence = (
            keyword_score * 0.25
            + indicator_score * 0.25
            + semantic_score * 0.20
            + context_score * 0.15
            + historical_score * 0.15
            - anti_pattern_penalty * 0.1
        )

        # Ensure confidence is between 0 and 1
        total_confidence = max(0.0, min(1.0, total_confidence))

        # Collect matching details
        matched_keywords = self._find_matched_keywords(pattern, task_description)
        matched_indicators = self._find_matched_indicators(pattern, task_description)
        anti_pattern_violations = self._find_anti_pattern_violations(
            pattern, task_description
        )

        # Generate suggestions
        suggested_modifications = self._generate_suggested_modifications(
            pattern, task_description, total_confidence
        )
        optimization_opportunities = self._identify_optimization_opportunities(
            pattern, task_context
        )

        return PatternMatch(
            pattern=pattern,
            confidence=total_confidence,
            context_relevance=context_score,
            historical_relevance=historical_score,
            semantic_similarity=semantic_score,
            matched_keywords=matched_keywords,
            matched_indicators=matched_indicators,
            anti_pattern_violations=anti_pattern_violations,
            suggested_modifications=suggested_modifications,
            optimization_opportunities=optimization_opportunities,
        )

    def _calculate_keyword_score(
        self, pattern: Pattern, task_description: str
    ) -> float:
        """Calculate keyword-based matching score"""
        if not pattern.keywords:
            return 0.0

        description_lower = task_description.lower()
        matched_keywords = 0

        for keyword in pattern.keywords:
            if keyword.lower() in description_lower:
                matched_keywords += 1

        return matched_keywords / len(pattern.keywords)

    def _calculate_indicator_score(
        self, pattern: Pattern, task_description: str
    ) -> float:
        """Calculate indicator-based matching score"""
        if not pattern.indicators:
            return 0.0

        description_lower = task_description.lower()
        matched_indicators = 0

        for indicator in pattern.indicators:
            if indicator.lower() in description_lower:
                matched_indicators += 1

        return matched_indicators / len(pattern.indicators)

    def _calculate_semantic_similarity(
        self, pattern: Pattern, task_description: str
    ) -> float:
        """Calculate semantic similarity using word vectors"""
        if not self.semantic_vectors:
            return 0.0

        # Extract words from task description
        words = re.findall(r"\b\w+\b", task_description.lower())

        # Calculate average similarity between task words and pattern keywords
        similarities = []

        for keyword in pattern.keywords:
            if keyword in self.semantic_vectors:
                keyword_vector = self.semantic_vectors[keyword]

                for word in words:
                    if word in self.semantic_vectors:
                        word_vector = self.semantic_vectors[word]
                        similarity = np.dot(keyword_vector, word_vector)
                        similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0

    def _calculate_context_relevance(
        self, pattern: Pattern, task_context: Dict[str, Any]
    ) -> float:
        """Calculate context-based relevance score"""
        if not task_context:
            return 0.5  # Neutral score when no context available

        relevance_score = 0.5  # Base score

        # Check file types
        if "file_types" in task_context:
            file_types = task_context["file_types"]

            # API patterns are more relevant for API-related files
            if (
                pattern.pattern_type == PatternType.IMPLEMENTATION
                and "api" in pattern.pattern_id
            ):
                if any(ft in ["js", "py", "java"] for ft in file_types):
                    relevance_score += 0.2

            # Testing patterns are more relevant when test files are involved
            if pattern.pattern_type == PatternType.TESTING:
                if any("test" in ft for ft in file_types):
                    relevance_score += 0.3

        # Check project phase
        if "project_phase" in task_context:
            phase = task_context["project_phase"]

            if phase == "design" and pattern.pattern_type == PatternType.ARCHITECTURAL:
                relevance_score += 0.2
            elif (
                phase == "implementation"
                and pattern.pattern_type == PatternType.IMPLEMENTATION
            ):
                relevance_score += 0.2
            elif (
                phase == "optimization"
                and pattern.pattern_type == PatternType.PERFORMANCE
            ):
                relevance_score += 0.2

        # Check team size
        if "team_size" in task_context:
            team_size = task_context["team_size"]

            # Microservice patterns are more relevant for larger teams
            if "microservice" in pattern.pattern_id and team_size > 5:
                relevance_score += 0.1

        return min(1.0, relevance_score)

    def _calculate_historical_relevance(
        self, pattern: Pattern, historical_context: List[str]
    ) -> float:
        """Calculate historical relevance based on similar past tasks"""
        if not historical_context:
            return 0.5  # Neutral score when no historical data

        # Check if this pattern was used in similar historical tasks
        historical_usage = 0

        for historical_task in historical_context:
            historical_patterns = self.recognize_patterns(historical_task)
            for hist_match in historical_patterns:
                if hist_match.pattern.pattern_id == pattern.pattern_id:
                    historical_usage += hist_match.confidence

        if historical_context:
            return min(1.0, historical_usage / len(historical_context))

        return 0.5

    def _calculate_anti_pattern_penalty(
        self, pattern: Pattern, task_description: str
    ) -> float:
        """Calculate penalty for anti-pattern violations"""
        if not pattern.anti_patterns:
            return 0.0

        description_lower = task_description.lower()
        violations = 0

        for anti_pattern in pattern.anti_patterns:
            if anti_pattern.lower() in description_lower:
                violations += 1

        return violations / len(pattern.anti_patterns) if pattern.anti_patterns else 0.0

    def _find_matched_keywords(
        self, pattern: Pattern, task_description: str
    ) -> List[str]:
        """Find which keywords matched in the task description"""
        matched = []
        description_lower = task_description.lower()

        for keyword in pattern.keywords:
            if keyword.lower() in description_lower:
                matched.append(keyword)

        return matched

    def _find_matched_indicators(
        self, pattern: Pattern, task_description: str
    ) -> List[str]:
        """Find which indicators matched in the task description"""
        matched = []
        description_lower = task_description.lower()

        for indicator in pattern.indicators:
            if indicator.lower() in description_lower:
                matched.append(indicator)

        return matched

    def _find_anti_pattern_violations(
        self, pattern: Pattern, task_description: str
    ) -> List[str]:
        """Find anti-pattern violations in the task description"""
        violations = []
        description_lower = task_description.lower()

        for anti_pattern in pattern.anti_patterns:
            if anti_pattern.lower() in description_lower:
                violations.append(anti_pattern)

        return violations

    def _generate_suggested_modifications(
        self, pattern: Pattern, task_description: str, confidence: float
    ) -> List[str]:
        """Generate suggestions for improving pattern alignment"""
        suggestions = []

        if confidence < 0.5:
            suggestions.append(f"Consider incorporating {pattern.name} principles")

        if confidence > 0.7:
            suggestions.extend(pattern.optimization_strategies)

        return suggestions

    def _identify_optimization_opportunities(
        self, pattern: Pattern, task_context: Dict[str, Any]
    ) -> List[str]:
        """Identify optimization opportunities based on pattern and context"""
        opportunities = []

        # Add pattern-specific optimizations
        opportunities.extend(pattern.optimization_strategies)

        # Add context-specific optimizations
        if task_context.get("parallel_execution_possible", False):
            if pattern.parallelization_potential > 0.7:
                opportunities.append("parallel_implementation_recommended")

        if task_context.get("performance_critical", False):
            if pattern.pattern_type == PatternType.PERFORMANCE:
                opportunities.append("performance_optimization_critical")

        return opportunities

    def _post_process_matches(
        self, matches: List[PatternMatch], task_description: str
    ) -> List[PatternMatch]:
        """Apply post-processing filters and enhancements to pattern matches"""

        # Remove very low confidence matches
        filtered_matches = [m for m in matches if m.confidence > 0.3]

        # Boost complementary patterns
        for i, match1 in enumerate(filtered_matches):
            for j, match2 in enumerate(filtered_matches):
                if i != j and self._are_complementary_patterns(
                    match1.pattern, match2.pattern
                ):
                    filtered_matches[i].confidence *= 1.1
                    filtered_matches[j].confidence *= 1.1

        # Normalize confidences to ensure they don't exceed 1.0
        for match in filtered_matches:
            match.confidence = min(1.0, match.confidence)

        # Re-sort by confidence
        filtered_matches.sort(key=lambda x: x.confidence, reverse=True)

        return filtered_matches[:10]  # Return top 10 matches

    def _are_complementary_patterns(self, pattern1: Pattern, pattern2: Pattern) -> bool:
        """Check if two patterns are complementary (work well together)"""
        complementary_pairs = [
            ("api_first_design", "test_driven_development"),
            ("microservice_decomposition", "event_driven_architecture"),
            ("caching_optimization", "database_optimization"),
            ("blue_green_deployment", "circuit_breaker"),
        ]

        pair = (pattern1.pattern_id, pattern2.pattern_id)
        reverse_pair = (pattern2.pattern_id, pattern1.pattern_id)

        return pair in complementary_pairs or reverse_pair in complementary_pairs

    def update_pattern_usage(
        self, pattern_id: str, success: bool, completion_time: float
    ):
        """Update historical data for a pattern based on actual usage"""
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.usage_count += 1
            pattern.last_used = datetime.now()

            # Update success rate (exponential moving average)
            alpha = 0.1  # Learning rate
            pattern.success_rate = (
                alpha * (1.0 if success else 0.0) + (1 - alpha) * pattern.success_rate
            )

            # Update average completion time
            pattern.average_completion_time = (
                alpha * completion_time + (1 - alpha) * pattern.average_completion_time
            )

            # Update historical data
            self.historical_data["pattern_usage"][pattern_id] += 1
            self.historical_data["pattern_success_rates"][pattern_id] = (
                pattern.success_rate
            )
            self.historical_data["pattern_completion_times"][pattern_id].append(
                completion_time
            )

    def get_pattern_recommendations(
        self, recognized_patterns: List[PatternMatch]
    ) -> Dict[str, Any]:
        """Generate comprehensive recommendations based on recognized patterns"""
        if not recognized_patterns:
            return {"recommendations": [], "risk_assessment": "UNKNOWN"}

        recommendations = []
        risk_factors = []
        optimization_strategies = []

        for match in recognized_patterns[:3]:  # Top 3 patterns
            pattern = match.pattern

            # Add pattern-specific recommendations
            if match.confidence > 0.7:
                recommendations.append(
                    {
                        "pattern": pattern.name,
                        "confidence": match.confidence,
                        "approach": pattern.recommended_approach,
                        "strategies": pattern.optimization_strategies,
                    }
                )

            # Collect risk factors
            if pattern.risk_level > 0.6:
                risk_factors.append(f"High risk pattern: {pattern.name}")

            # Collect optimization strategies
            optimization_strategies.extend(pattern.optimization_strategies)

        # Assess overall risk
        avg_risk = np.mean([m.pattern.risk_level for m in recognized_patterns[:3]])
        if avg_risk > 0.7:
            risk_assessment = "HIGH"
        elif avg_risk > 0.5:
            risk_assessment = "MEDIUM"
        else:
            risk_assessment = "LOW"

        return {
            "recommendations": recommendations,
            "risk_assessment": risk_assessment,
            "risk_factors": risk_factors,
            "optimization_strategies": list(set(optimization_strategies)),
            "parallelization_potential": np.mean(
                [m.pattern.parallelization_potential for m in recognized_patterns[:3]]
            ),
            "estimated_complexity_multiplier": np.mean(
                [m.pattern.complexity_multiplier for m in recognized_patterns[:3]]
            ),
            "estimated_time_multiplier": np.mean(
                [m.pattern.time_multiplier for m in recognized_patterns[:3]]
            ),
        }


class ContextAnalyzer:
    """Analyzes task context for better pattern recognition"""

    def analyze_file_context(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze file context from file paths"""
        context = {"file_types": [], "directories": [], "modification_scope": "local"}

        file_extensions = []
        directories = set()

        for file_path in file_paths:
            if "." in file_path:
                ext = file_path.split(".")[-1]
                file_extensions.append(ext)

            if "/" in file_path:
                dir_path = "/".join(file_path.split("/")[:-1])
                directories.add(dir_path)

        context["file_types"] = list(set(file_extensions))
        context["directories"] = list(directories)

        if len(directories) > 3:
            context["modification_scope"] = "global"
        elif len(directories) > 1:
            context["modification_scope"] = "module"
        else:
            context["modification_scope"] = "local"

        return context


class PerformancePatternPredictor:
    """Predicts performance characteristics based on recognized patterns"""

    def predict_performance_impact(
        self, patterns: List[PatternMatch]
    ) -> Dict[str, float]:
        """Predict performance impact of recognized patterns"""
        if not patterns:
            return {"complexity_multiplier": 1.0, "time_multiplier": 1.0}

        # Calculate weighted averages based on confidence
        total_confidence = sum(p.confidence for p in patterns)

        if total_confidence == 0:
            return {"complexity_multiplier": 1.0, "time_multiplier": 1.0}

        complexity_multiplier = (
            sum(p.pattern.complexity_multiplier * p.confidence for p in patterns)
            / total_confidence
        )

        time_multiplier = (
            sum(p.pattern.time_multiplier * p.confidence for p in patterns)
            / total_confidence
        )

        return {
            "complexity_multiplier": complexity_multiplier,
            "time_multiplier": time_multiplier,
            "parallelization_potential": sum(
                p.pattern.parallelization_potential * p.confidence for p in patterns
            )
            / total_confidence,
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize pattern recognition system
    pattern_system = TaskPatternRecognitionSystem()

    # Test pattern recognition
    test_description = """
    Implement a microservice architecture with API-first design.
    The system should use event-driven communication between services
    and include comprehensive testing with test-driven development.
    Performance optimization with caching is also required.
    """

    test_context = {
        "file_types": ["py", "js", "yaml"],
        "project_phase": "design",
        "team_size": 8,
        "performance_critical": True,
    }

    # Recognize patterns
    patterns = pattern_system.recognize_patterns(test_description, test_context)

    # Print results
    print("Recognized Patterns:")
    for i, match in enumerate(patterns[:5], 1):
        print(f"{i}. {match.pattern.name} (confidence: {match.confidence:.2f})")
        print(f"   Type: {match.pattern.pattern_type}")
        print(f"   Matched keywords: {match.matched_keywords}")
        print(f"   Optimization opportunities: {match.optimization_opportunities}")
        print()

    # Get recommendations
    recommendations = pattern_system.get_pattern_recommendations(patterns)
    print("Recommendations:")
    print(f"Risk Assessment: {recommendations['risk_assessment']}")
    print(
        f"Parallelization Potential: {recommendations['parallelization_potential']:.2f}"
    )
    print(
        f"Complexity Multiplier: {recommendations['estimated_complexity_multiplier']:.2f}"
    )
    print(f"Time Multiplier: {recommendations['estimated_time_multiplier']:.2f}")
