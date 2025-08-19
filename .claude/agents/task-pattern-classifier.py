from typing import Any, Dict, List

"""
Task Pattern Classification System with Machine Learning
Part of the Enhanced Task Decomposition Analyzer

This module provides ML-based task pattern recognition and optimization
for the Gadugi multi-agent system.
"""
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter, defaultdict

class TaskType(Enum):
    """Primary task type classifications"""

    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    TEST_COVERAGE = "test_coverage"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    OPTIMIZATION = "optimization"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    MAINTENANCE = "maintenance"

class ComplexityLevel(Enum):
    """Task complexity levels"""

    TRIVIAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

@dataclass
class TaskFeatures:
    """Feature vector for ML task classification"""

    # Text-based features
    description_length: int = 0
    keyword_counts: Dict[str, int] = field(default_factory=dict)
    complexity_indicators: List[str] = field(default_factory=list)
    technical_depth_score: float = 0.0

    # File-based features
    file_count: int = 0
    file_types: Dict[str, int] = field(default_factory=dict)
    directory_count: int = 0
    modification_scope: str = "local"  # local, module, system, global

    # Dependency features
    dependency_count: int = 0
    external_dependency_count: int = 0
    api_interaction_count: int = 0
    database_interaction: bool = False

    # Historical features
    similar_task_count: int = 0
    historical_success_rate: float = 0.0
    average_completion_time: float = 0.0
    typical_complexity: ComplexityLevel = ComplexityLevel.MEDIUM

    # Semantic features
    has_testing_requirements: bool = False
    has_documentation_requirements: bool = False
    has_security_implications: bool = False
    has_performance_requirements: bool = False
    has_integration_requirements: bool = False

@dataclass
class TaskClassification:
    """Task classification result"""

    primary_type: TaskType
    subtypes: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    confidence: float = 0.0
    complexity_scores: Dict[str, float] = field(default_factory=dict)
    optimizations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    recommended_approach: str = ""

class TaskPatternClassifier:
    """
    ML-based task pattern recognition and classification system.

    Uses feature extraction and pattern matching to classify tasks,
    predict complexity, and suggest optimization strategies.
    """

    def __init__(self):
        self.keyword_patterns = self._initialize_keyword_patterns()
        self.complexity_indicators = self._initialize_complexity_indicators()
        self.pattern_library = self._initialize_pattern_library()
        self.historical_data = self._initialize_historical_data()

    def _initialize_keyword_patterns(self) -> Dict[TaskType, List[str]]:
        """Initialize keyword patterns for task type classification"""
        return {
            TaskType.FEATURE: [
                "implement",
                "add",
                "create",
                "build",
                "develop",
                "feature",
                "functionality",
                "capability",
                "enhancement",
                "new",
            ],
            TaskType.BUG_FIX: [
                "fix",
                "bug",
                "error",
                "issue",
                "problem",
                "resolve",
                "correct",
                "repair",
                "debug",
                "crash",
                "exception",
            ],
            TaskType.TEST_COVERAGE: [
                "test",
                "testing",
                "coverage",
                "unit test",
                "integration test",
                "e2e",
                "mock",
                "assert",
                "verify",
                "validate",
            ],
            TaskType.REFACTORING: [
                "refactor",
                "cleanup",
                "restructure",
                "reorganize",
                "improve",
                "optimize code",
                "clean up",
                "modernize",
            ],
            TaskType.DOCUMENTATION: [
                "document",
                "docs",
                "readme",
                "guide",
                "tutorial",
                "comments",
                "docstring",
                "explain",
                "describe",
            ],
            TaskType.RESEARCH: [
                "research",
                "investigate",
                "explore",
                "analyze",
                "study",
                "evaluate",
                "assess",
                "compare",
                "feasibility",
            ],
            TaskType.OPTIMIZATION: [
                "optimize",
                "performance",
                "speed up",
                "improve performance",
                "faster",
                "efficient",
                "reduce latency",
                "scale",
            ],
            TaskType.INFRASTRUCTURE: [
                "infrastructure",
                "deployment",
                "ci/cd",
                "pipeline",
                "docker",
                "kubernetes",
                "aws",
                "cloud",
                "devops",
            ],
            TaskType.SECURITY: [
                "security",
                "authentication",
                "authorization",
                "encrypt",
                "secure",
                "vulnerability",
                "safety",
                "protection",
            ],
            TaskType.MAINTENANCE: [
                "maintenance",
                "update",
                "upgrade",
                "migrate",
                "deprecate",
                "remove",
                "cleanup",
                "housekeeping",
            ],
        }

    def _initialize_complexity_indicators(self) -> Dict[str, float]:
        """Initialize complexity scoring indicators"""
        return {
            # High complexity indicators
            "machine learning": 4.5,
            "artificial intelligence": 4.5,
            "distributed system": 4.0,
            "microservices": 4.0,
            "real-time": 4.0,
            "concurrent": 3.8,
            "parallel": 3.8,
            "async": 3.5,
            "database schema": 3.5,
            "api design": 3.0,
            # Medium complexity indicators
            "integration": 2.8,
            "authentication": 2.5,
            "caching": 2.5,
            "workflow": 2.3,
            "validation": 2.0,
            # Low complexity indicators
            "ui update": 1.5,
            "text change": 1.2,
            "configuration": 1.8,
            "documentation": 1.0,
            "logging": 1.3,
        }

    def _initialize_pattern_library(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pattern library for task optimization"""
        return {
            "test_driven_development": {
                "indicators": ["test", "tdd", "unit test", "coverage"],
                "optimization": "parallel_test_execution",
                "complexity_multiplier": 1.2,
                "estimated_overhead": 0.15,
            },
            "api_development": {
                "indicators": ["api", "endpoint", "rest", "graphql"],
                "optimization": "api_first_design",
                "complexity_multiplier": 1.4,
                "estimated_overhead": 0.25,
            },
            "database_migration": {
                "indicators": ["migration", "schema", "database", "table"],
                "optimization": "staged_migration",
                "complexity_multiplier": 1.8,
                "estimated_overhead": 0.35,
            },
            "ui_component": {
                "indicators": ["component", "ui", "frontend", "react", "vue"],
                "optimization": "component_isolation",
                "complexity_multiplier": 1.1,
                "estimated_overhead": 0.10,
            },
            "security_implementation": {
                "indicators": ["security", "auth", "encrypt", "secure"],
                "optimization": "security_first_approach",
                "complexity_multiplier": 1.6,
                "estimated_overhead": 0.30,
            },
        }

    def _initialize_historical_data(self) -> Dict[str, Any]:
        """Initialize historical task data for pattern learning"""
        # In a real implementation, this would load from a database
        # For now, we'll use synthetic data patterns
        return {
            "completion_times": defaultdict(list),
            "success_rates": defaultdict(float),
            "complexity_distributions": defaultdict(dict),
            "common_patterns": defaultdict(int),
        }

    def extract_features(
        self,
        task_description: str,
        target_files: List[str] = None,
        dependencies: List[str] = None,
    ) -> TaskFeatures:
        """
        Extract comprehensive features from task description and metadata.

        Args:
            task_description: Text description of the task
            target_files: List of files that will be modified
            dependencies: List of dependencies

        Returns:
            TaskFeatures object with extracted features
        """
        target_files = target_files or []
        dependencies = dependencies or []

        features = TaskFeatures()

        # Text-based feature extraction
        features.description_length = len(task_description)
        features.keyword_counts = self._count_keywords(task_description)
        features.complexity_indicators = self._extract_complexity_indicators(
            task_description
        )
        features.technical_depth_score = self._calculate_technical_depth(
            task_description
        )

        # File-based feature extraction
        features.file_count = len(target_files)
        features.file_types = self._analyze_file_types(target_files)
        features.directory_count = len(set(self._get_directories(target_files)))
        features.modification_scope = self._determine_modification_scope(target_files)

        # Dependency feature extraction
        features.dependency_count = len(dependencies)
        features.external_dependency_count = self._count_external_dependencies(
            dependencies
        )
        features.api_interaction_count = self._count_api_interactions(task_description)
        features.database_interaction = self._has_database_interaction(task_description)

        # Historical feature extraction
        similar_tasks = self._find_similar_tasks(task_description)
        features.similar_task_count = len(similar_tasks)
        if similar_tasks:
            features.historical_success_rate = self._calculate_success_rate(
                similar_tasks
            )
            features.average_completion_time = self._calculate_average_time(
                similar_tasks
            )
            features.typical_complexity = self._get_typical_complexity(similar_tasks)

        # Semantic feature extraction
        features.has_testing_requirements = self._has_testing_requirements(
            task_description
        )
        features.has_documentation_requirements = self._has_documentation_requirements(
            task_description
        )
        features.has_security_implications = self._has_security_implications(
            task_description
        )
        features.has_performance_requirements = self._has_performance_requirements(
            task_description
        )
        features.has_integration_requirements = self._has_integration_requirements(
            task_description
        )

        return features

    def classify_task(self, features: TaskFeatures) -> TaskClassification:
        """
        Classify task based on extracted features.

        Args:
            features: TaskFeatures object

        Returns:
            TaskClassification with predicted type and metadata
        """
        # Primary type classification
        type_scores = self._calculate_type_scores(features)
        primary_type = max(type_scores.items(), key=lambda x: x[1])[0]
        confidence = type_scores[primary_type] / sum(type_scores.values())

        # Subtype classification
        subtypes = self._identify_subtypes(features, primary_type)

        # Pattern recognition
        patterns = self._identify_patterns(features)

        # Complexity scoring
        complexity_scores = self._calculate_complexity_scores(features)

        # Optimization suggestions
        optimizations = self._suggest_optimizations(features, patterns)

        # Risk factor identification
        risk_factors = self._identify_risk_factors(features, complexity_scores)

        # Recommended approach
        recommended_approach = self._recommend_approach(
            features, primary_type, complexity_scores
        )

        return TaskClassification(
            primary_type=primary_type,
            subtypes=subtypes,
            patterns=patterns,
            confidence=confidence,
            complexity_scores=complexity_scores,
            optimizations=optimizations,
            risk_factors=risk_factors,
            recommended_approach=recommended_approach,
        )

    def _count_keywords(self, description: str) -> Dict[str, int]:
        """Count occurrences of task-type keywords"""
        description_lower = description.lower()
        keyword_counts = {}

        for task_type, keywords in self.keyword_patterns.items():
            count = sum(description_lower.count(keyword) for keyword in keywords)
            keyword_counts[task_type.value] = count

        return keyword_counts

    def _extract_complexity_indicators(self, description: str) -> List[str]:
        """Extract complexity indicators from description"""
        description_lower = description.lower()
        indicators = []

        for indicator, _score in self.complexity_indicators.items():
            if indicator in description_lower:
                indicators.append(indicator)

        return indicators

    def _calculate_technical_depth(self, description: str) -> float:
        """Calculate technical depth score based on technical terms"""
        technical_terms = [
            "architecture",
            "algorithm",
            "data structure",
            "design pattern",
            "scalability",
            "concurrency",
            "optimization",
            "complexity",
        ]

        description_lower = description.lower()
        score = sum(description_lower.count(term) for term in technical_terms)

        # Normalize by description length
        return min(score / (len(description.split()) / 100), 5.0)

    def _analyze_file_types(self, target_files: List[str]) -> Dict[str, int]:
        """Analyze file types in target files"""
        file_types = defaultdict(int)

        for file_path in target_files:
            if "." in file_path:
                extension = file_path.split(".")[-1].lower()
                file_types[extension] += 1
            else:
                file_types["no_extension"] += 1

        return dict(file_types)

    def _get_directories(self, target_files: List[str]) -> List[str]:
        """Get list of directories from file paths"""
        directories = []
        for file_path in target_files:
            if "/" in file_path:
                directory = "/".join(file_path.split("/")[:-1])
                directories.append(directory)
        return directories

    def _determine_modification_scope(self, target_files: List[str]) -> str:
        """Determine the scope of modifications"""
        if not target_files:
            return "unknown"

        directories = set(self._get_directories(target_files))

        if len(directories) == 0:
            return "local"
        elif len(directories) == 1:
            return "module"
        elif len(directories) <= 3:
            return "system"
        else:
            return "global"

    def _count_external_dependencies(self, dependencies: List[str]) -> int:
        """Count external dependencies (not internal modules)"""
        external_indicators = ["http", "api", "service", "external", "third-party"]
        count = 0

        for dep in dependencies:
            dep_lower = dep.lower()
            if any(indicator in dep_lower for indicator in external_indicators):
                count += 1

        return count

    def _count_api_interactions(self, description: str) -> int:
        """Count API interaction references in description"""
        api_terms = ["api", "endpoint", "request", "response", "rest", "graphql"]
        description_lower = description.lower()

        return sum(description_lower.count(term) for term in api_terms)

    def _has_database_interaction(self, description: str) -> bool:
        """Check if task involves database interactions"""
        db_terms = ["database", "db", "sql", "query", "table", "schema", "migration"]
        description_lower = description.lower()

        return any(term in description_lower for term in db_terms)

    def _find_similar_tasks(self, description: str) -> List[str]:
        """Find similar tasks from historical data"""
        # Simple similarity based on keyword overlap
        # In a real implementation, this would use more sophisticated similarity measures
        description_words = set(description.lower().split())
        similar_tasks = []

        for task_id, task_data in self.historical_data.get(
            "task_descriptions", {}
        ).items():
            task_words = set(task_data.lower().split())
            overlap = len(description_words & task_words)

            if overlap >= 3:  # Minimum overlap threshold
                similar_tasks.append(task_id)

        return similar_tasks

    def _calculate_success_rate(self, similar_tasks: List[str]) -> float:
        """Calculate success rate from similar tasks"""
        if not similar_tasks:
            return 0.8  # Default success rate

        success_count = sum(
            1
            for task_id in similar_tasks
            if self.historical_data.get("success_status", {}).get(task_id, True)
        )

        return success_count / len(similar_tasks)

    def _calculate_average_time(self, similar_tasks: List[str]) -> float:
        """Calculate average completion time from similar tasks"""
        if not similar_tasks:
            return 60.0  # Default 60 minutes

        times = [
            self.historical_data.get("completion_times", {}).get(task_id, 60)
            for task_id in similar_tasks
        ]

        return sum(times) / len(times)

    def _get_typical_complexity(self, similar_tasks: List[str]) -> ComplexityLevel:
        """Get typical complexity level from similar tasks"""
        if not similar_tasks:
            return ComplexityLevel.MEDIUM

        complexities = [
            self.historical_data.get("complexities", {}).get(
                task_id, ComplexityLevel.MEDIUM
            )
            for task_id in similar_tasks
        ]

        # Return most common complexity
        complexity_counts = Counter(complexities)
        return complexity_counts.most_common(1)[0][0]

    def _has_testing_requirements(self, description: str) -> bool:
        """Check if task has testing requirements"""
        test_terms = ["test", "testing", "coverage", "unit test", "integration test"]
        description_lower = description.lower()
        return any(term in description_lower for term in test_terms)

    def _has_documentation_requirements(self, description: str) -> bool:
        """Check if task has documentation requirements"""
        doc_terms = ["document", "docs", "readme", "guide", "documentation"]
        description_lower = description.lower()
        return any(term in description_lower for term in doc_terms)

    def _has_security_implications(self, description: str) -> bool:
        """Check if task has security implications"""
        security_terms = ["security", "auth", "encrypt", "secure", "vulnerability"]
        description_lower = description.lower()
        return any(term in description_lower for term in security_terms)

    def _has_performance_requirements(self, description: str) -> bool:
        """Check if task has performance requirements"""
        perf_terms = ["performance", "speed", "optimize", "fast", "efficient"]
        description_lower = description.lower()
        return any(term in description_lower for term in perf_terms)

    def _has_integration_requirements(self, description: str) -> bool:
        """Check if task has integration requirements"""
        integration_terms = ["integrate", "integration", "connect", "interface"]
        description_lower = description.lower()
        return any(term in description_lower for term in integration_terms)

    def _calculate_type_scores(self, features: TaskFeatures) -> Dict[TaskType, float]:
        """Calculate probability scores for each task type"""
        scores = {}

        for task_type in TaskType:
            score = 0.0

            # Keyword-based scoring
            keyword_count = features.keyword_counts.get(task_type.value, 0)
            score += keyword_count * 2.0

            # Feature-based scoring
            if (
                task_type == TaskType.TEST_COVERAGE
                and features.has_testing_requirements
            ):
                score += 3.0
            elif (
                task_type == TaskType.DOCUMENTATION
                and features.has_documentation_requirements
            ):
                score += 3.0
            elif task_type == TaskType.SECURITY and features.has_security_implications:
                score += 3.0
            elif (
                task_type == TaskType.OPTIMIZATION
                and features.has_performance_requirements
            ):
                score += 3.0

            # File type scoring
            if task_type == TaskType.TEST_COVERAGE:
                test_files = features.file_types.get(
                    "test", 0
                ) + features.file_types.get("spec", 0)
                score += test_files * 1.5

            scores[task_type] = max(score, 0.1)  # Minimum score

        return scores

    def _identify_subtypes(
        self, features: TaskFeatures, primary_type: TaskType
    ) -> List[str]:
        """Identify task subtypes based on features"""
        subtypes = []

        if primary_type == TaskType.TEST_COVERAGE:
            if "unit" in " ".join(features.complexity_indicators):
                subtypes.append("unit_testing")
            if "integration" in " ".join(features.complexity_indicators):
                subtypes.append("integration_testing")
            if features.has_integration_requirements:
                subtypes.append("e2e_testing")

        elif primary_type == TaskType.FEATURE:
            if features.has_integration_requirements:
                subtypes.append("integration_feature")
            if features.database_interaction:
                subtypes.append("data_feature")
            if features.api_interaction_count > 0:
                subtypes.append("api_feature")

        elif primary_type == TaskType.BUG_FIX:
            if features.has_security_implications:
                subtypes.append("security_fix")
            if features.has_performance_requirements:
                subtypes.append("performance_fix")
            if features.database_interaction:
                subtypes.append("data_fix")

        return subtypes

    def _identify_patterns(self, features: TaskFeatures) -> List[str]:
        """Identify applicable patterns from pattern library"""
        patterns = []

        description_text = " ".join(features.complexity_indicators).lower()

        for pattern_name, pattern_data in self.pattern_library.items():
            indicators = pattern_data["indicators"]
            if any(indicator in description_text for indicator in indicators):
                patterns.append(pattern_name)

        return patterns

    def _calculate_complexity_scores(self, features: TaskFeatures) -> Dict[str, float]:
        """Calculate multi-dimensional complexity scores"""
        scores = {}

        # Technical complexity
        technical_score = 1.0
        technical_score += features.technical_depth_score
        technical_score += len(features.complexity_indicators) * 0.5
        technical_score += features.dependency_count * 0.2
        scores["technical"] = min(technical_score, 5.0)

        # Domain complexity
        domain_score = 1.0
        if features.has_security_implications:
            domain_score += 1.5
        if features.database_interaction:
            domain_score += 1.0
        if features.api_interaction_count > 0:
            domain_score += features.api_interaction_count * 0.3
        scores["domain"] = min(domain_score, 5.0)

        # Integration complexity
        integration_score = 1.0
        integration_score += features.external_dependency_count * 0.5
        if features.has_integration_requirements:
            integration_score += 1.0
        if features.modification_scope == "global":
            integration_score += 1.5
        elif features.modification_scope == "system":
            integration_score += 1.0
        scores["integration"] = min(integration_score, 5.0)

        # Knowledge complexity
        knowledge_score = 1.0
        if features.similar_task_count == 0:
            knowledge_score += 2.0
        elif features.similar_task_count < 3:
            knowledge_score += 1.0
        if features.historical_success_rate < 0.7:
            knowledge_score += 1.0
        scores["knowledge"] = min(knowledge_score, 5.0)

        # Overall complexity (weighted average)
        scores["overall"] = (
            scores["technical"] * 0.3
            + scores["domain"] * 0.25
            + scores["integration"] * 0.25
            + scores["knowledge"] * 0.2
        )

        return scores

    def _suggest_optimizations(
        self, features: TaskFeatures, patterns: List[str]
    ) -> List[str]:
        """Suggest optimization strategies based on features and patterns"""
        optimizations = []

        # Pattern-based optimizations
        for pattern in patterns:
            if pattern in self.pattern_library:
                optimization = self.pattern_library[pattern]["optimization"]
                optimizations.append(optimization)

        # Feature-based optimizations
        if features.has_testing_requirements and features.file_count > 3:
            optimizations.append("parallel_test_execution")

        if features.modification_scope == "global":
            optimizations.append("phased_implementation")

        if features.external_dependency_count > 2:
            optimizations.append("dependency_isolation")

        if features.complexity_scores.get("overall", 0) > 4.0:  # type: ignore
            optimizations.append("task_decomposition")

        return list(set(optimizations))  # Remove duplicates

    def _identify_risk_factors(
        self, features: TaskFeatures, complexity_scores: Dict[str, float]
    ) -> List[str]:
        """Identify potential risk factors"""
        risks = []

        if complexity_scores.get("overall", 0) > 4.0:
            risks.append("high_complexity")

        if features.historical_success_rate < 0.6:
            risks.append("low_historical_success_rate")

        if features.similar_task_count == 0:
            risks.append("novel_task_domain")

        if features.external_dependency_count > 3:
            risks.append("high_external_dependencies")

        if features.has_security_implications:
            risks.append("security_sensitive")

        if features.modification_scope == "global":
            risks.append("wide_modification_scope")

        return risks

    def _recommend_approach(
        self,
        features: TaskFeatures,
        primary_type: TaskType,
        complexity_scores: Dict[str, float],
    ) -> str:
        """Recommend implementation approach"""
        overall_complexity = complexity_scores.get("overall", 3.0)

        if overall_complexity < 2.0:
            return "direct_implementation"
        elif overall_complexity < 3.5:
            if features.has_testing_requirements:
                return "test_driven_development"
            else:
                return "iterative_implementation"
        elif overall_complexity < 4.5:
            return "phased_implementation_with_prototyping"
        else:
            return "research_and_decomposition_required"

    def optimize_for_patterns(self, task_analysis: Any) -> List[str]:
        """Generate pattern-based optimizations for a task analysis"""
        optimizations = []

        # Extract patterns from task analysis
        if hasattr(task_analysis, "classification"):
            patterns = task_analysis.classification.patterns

            for pattern in patterns:
                if pattern in self.pattern_library:
                    pattern_data = self.pattern_library[pattern]
                    optimization = pattern_data["optimization"]
                    optimizations.append(optimization)

        return optimizations

# Example usage and testing
if __name__ == "__main__":
    # Initialize classifier
    classifier = TaskPatternClassifier()

    # Test task classification
    test_description = """
    Implement machine learning model for code pattern recognition.
    This task involves creating a neural network that can analyze code
    patterns and suggest optimizations. The implementation should include
    comprehensive unit tests and integration with the existing API.
    """

    test_files = [
        "ml_models/pattern_recognizer.py",
        "tests/test_pattern_recognizer.py",
        "api/ml_endpoints.py",
    ]

    test_dependencies = ["tensorflow", "scikit-learn", "api_service"]

    # Extract features
    features = classifier.extract_features(
        test_description, test_files, test_dependencies
    )

    # Classify task
    classification = classifier.classify_task(features)

    # Print results
    print("Task Classification Results:")
    print(f"Primary Type: {classification.primary_type}")
    print(f"Confidence: {classification.confidence:.2f}")
    print(f"Subtypes: {classification.subtypes}")
    print(f"Patterns: {classification.patterns}")
    print(f"Complexity Scores: {classification.complexity_scores}")
    print(f"Optimizations: {classification.optimizations}")
    print(f"Risk Factors: {classification.risk_factors}")
    print(f"Recommended Approach: {classification.recommended_approach}")
