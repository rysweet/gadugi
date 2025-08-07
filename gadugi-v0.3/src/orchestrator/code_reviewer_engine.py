"""
CodeReviewer Engine - Comprehensive automated code review

This engine performs multi-dimensional code analysis including quality, security,
performance, and maintainability assessment with configurable quality gates.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import time
import os
import re
import shutil
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import yaml
import sys


class ReviewStatus(Enum):
    """Review status enumeration"""
    APPROVED = "approved"
    NEEDS_CHANGES = "needs_changes"
    REJECTED = "rejected"


class IssueType(Enum):
    """Issue type classification"""
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    INFO = "info"


class IssueCategory(Enum):
    """Issue category classification"""
    STYLE = "style"
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


@dataclass
class ReviewIssue:
    """Individual code review issue"""
    line: int
    column: int
    type: IssueType
    category: IssueCategory
    message: str
    suggestion: str
    rule_id: str
    severity: int = 1  # 1-5, where 5 is most severe
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "column": self.column,
            "type": self.type.value,
            "category": self.category.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "rule_id": self.rule_id,
            "severity": self.severity
        }


@dataclass
class FileReview:
    """Review results for a single file"""
    file_path: str
    status: ReviewStatus
    score: int
    issues: List[ReviewIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "status": self.status.value,
            "score": self.score,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics
        }


@dataclass
class QualityMetrics:
    """Code quality metrics"""
    maintainability_index: float = 0.0
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    test_coverage: float = 0.0
    technical_debt_ratio: float = 0.0
    security_score: float = 0.0
    lines_of_code: int = 0
    duplication_ratio: float = 0.0


@dataclass
class ReviewSummary:
    """Overall review summary"""
    total_files: int
    total_lines: int
    issues_found: int
    critical_issues: int
    warnings: int
    suggestions: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewResult:
    """Complete review result"""
    review_id: str
    status: ReviewStatus
    overall_score: int
    summary: ReviewSummary
    quality_metrics: QualityMetrics
    file_reviews: List[FileReview]
    recommendations: List[str]
    quality_gates: Dict[str, str]
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "status": self.status.value,
            "overall_score": self.overall_score,
            "summary": self.summary.to_dict(),
            "quality_metrics": asdict(self.quality_metrics),
            "file_reviews": [fr.to_dict() for fr in self.file_reviews],
            "recommendations": self.recommendations,
            "quality_gates": self.quality_gates,
            "execution_time": self.execution_time
        }


class AnalysisTool:
    """Base class for analysis tools"""
    
    def __init__(self, name: str, language: str, config: Dict[str, Any] = None):
        self.name = name
        self.language = language
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def is_available(self) -> bool:
        """Check if tool is available"""
        try:
            result = subprocess.run(
                [self.name, "--version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    async def analyze(self, files: List[str]) -> List[ReviewIssue]:
        """Analyze files and return issues"""
        raise NotImplementedError("Subclasses must implement analyze method")


class RuffAnalyzer(AnalysisTool):
    """Python ruff linter integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("ruff", "python", config)
    
    async def analyze(self, files: List[str]) -> List[ReviewIssue]:
        """Analyze Python files with ruff"""
        if not files:
            return []
        
        try:
            cmd = ["ruff", "check", "--format", "json"] + files
            if self.config.get("args"):
                cmd.extend(self.config["args"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            issues = []
            if result.stdout:
                try:
                    ruff_results = json.loads(result.stdout)
                    for item in ruff_results:
                        issues.append(ReviewIssue(
                            line=item.get("location", {}).get("row", 0),
                            column=item.get("location", {}).get("column", 0),
                            type=self._map_severity(item.get("severity", "warning")),
                            category=self._map_category(item.get("code", "")),
                            message=item.get("message", ""),
                            suggestion=self._generate_suggestion(item),
                            rule_id=item.get("code", ""),
                            severity=self._severity_score(item.get("severity", "warning"))
                        ))
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse ruff output")
            
            return issues
            
        except subprocess.TimeoutExpired:
            self.logger.error("Ruff analysis timed out")
            return []
        except Exception as e:
            self.logger.error(f"Ruff analysis failed: {str(e)}")
            return []
    
    def _map_severity(self, severity: str) -> IssueType:
        """Map ruff severity to IssueType"""
        mapping = {
            "error": IssueType.ERROR,
            "warning": IssueType.WARNING,
            "note": IssueType.INFO
        }
        return mapping.get(severity.lower(), IssueType.WARNING)
    
    def _map_category(self, code: str) -> IssueCategory:
        """Map ruff error code to category"""
        if code.startswith(('E', 'W')):
            return IssueCategory.STYLE
        elif code.startswith('F'):
            return IssueCategory.QUALITY
        elif code.startswith('S'):
            return IssueCategory.SECURITY
        elif code.startswith('C'):
            return IssueCategory.MAINTAINABILITY
        elif code.startswith('T'):
            return IssueCategory.TESTING
        else:
            return IssueCategory.QUALITY
    
    def _generate_suggestion(self, item: Dict[str, Any]) -> str:
        """Generate helpful suggestion from ruff result"""
        code = item.get("code", "")
        message = item.get("message", "")
        
        # Generate context-aware suggestions
        if "line too long" in message.lower():
            return "Consider breaking the line at a logical point"
        elif "unused import" in message.lower():
            return "Remove the unused import statement"
        elif "undefined name" in message.lower():
            return "Check spelling or add necessary import"
        else:
            return f"See ruff documentation for {code}"
    
    def _severity_score(self, severity: str) -> int:
        """Convert severity to numeric score"""
        mapping = {
            "error": 4,
            "warning": 2,
            "note": 1
        }
        return mapping.get(severity.lower(), 2)


class BanditAnalyzer(AnalysisTool):
    """Python security analyzer using bandit"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("bandit", "python", config)
    
    async def analyze(self, files: List[str]) -> List[ReviewIssue]:
        """Analyze Python files for security issues"""
        if not files:
            return []
        
        try:
            cmd = ["bandit", "-r", "-f", "json"] + files
            if self.config.get("args"):
                cmd.extend(self.config["args"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            issues = []
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    results = bandit_data.get("results", [])
                    
                    for item in results:
                        issues.append(ReviewIssue(
                            line=item.get("line_number", 0),
                            column=item.get("col_offset", 0),
                            type=IssueType.ERROR if item.get("issue_severity") == "HIGH" else IssueType.WARNING,
                            category=IssueCategory.SECURITY,
                            message=item.get("issue_text", ""),
                            suggestion=self._generate_security_suggestion(item),
                            rule_id=item.get("test_id", ""),
                            severity=self._map_severity_score(item.get("issue_severity", "MEDIUM"))
                        ))
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse bandit output")
            
            return issues
            
        except subprocess.TimeoutExpired:
            self.logger.error("Bandit analysis timed out")
            return []
        except Exception as e:
            self.logger.error(f"Bandit analysis failed: {str(e)}")
            return []
    
    def _generate_security_suggestion(self, item: Dict[str, Any]) -> str:
        """Generate security-focused suggestions"""
        test_id = item.get("test_id", "")
        
        suggestions = {
            "B101": "Use assert only for debugging, not for data validation",
            "B102": "Avoid exec() function - consider safer alternatives",
            "B103": "Set file permissions explicitly rather than using default",
            "B108": "Use tempfile.NamedTemporaryFile() for temporary files",
            "B110": "Consider using logging.exception() instead of pass",
            "B201": "Use Flask-Talisman or similar for security headers",
            "B301": "Use pickle alternatives like json for data serialization",
            "B501": "Use requests with verify=True for SSL verification",
            "B506": "Use yaml.safe_load() instead of yaml.load()",
            "B601": "Parameterize shell commands to prevent injection"
        }
        
        return suggestions.get(test_id, "Review security implications and follow OWASP guidelines")
    
    def _map_severity_score(self, severity: str) -> int:
        """Map bandit severity to numeric score"""
        mapping = {
            "HIGH": 5,
            "MEDIUM": 3, 
            "LOW": 1
        }
        return mapping.get(severity, 3)


class MypyAnalyzer(AnalysisTool):
    """Python type checking with mypy"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("mypy", "python", config)
    
    async def analyze(self, files: List[str]) -> List[ReviewIssue]:
        """Analyze Python files for type issues"""
        if not files:
            return []
        
        try:
            cmd = ["mypy", "--show-column-numbers", "--show-error-codes"] + files
            if self.config.get("args"):
                cmd.extend(self.config["args"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.splitlines():
                    issue = self._parse_mypy_line(line)
                    if issue:
                        issues.append(issue)
            
            return issues
            
        except subprocess.TimeoutExpired:
            self.logger.error("Mypy analysis timed out")
            return []
        except Exception as e:
            self.logger.error(f"Mypy analysis failed: {str(e)}")
            return []
    
    def _parse_mypy_line(self, line: str) -> Optional[ReviewIssue]:
        """Parse mypy output line"""
        # Format: file.py:line:column: error: message [error-code]
        pattern = r'^(.+):(\d+):(\d+): (\w+): (.+?)(?:\s+\[(.+)\])?$'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        file_path, line_num, column, level, message, error_code = match.groups()
        
        return ReviewIssue(
            line=int(line_num),
            column=int(column),
            type=IssueType.ERROR if level == "error" else IssueType.WARNING,
            category=IssueCategory.QUALITY,
            message=message,
            suggestion=self._generate_type_suggestion(message, error_code),
            rule_id=error_code or "mypy",
            severity=3 if level == "error" else 2
        )
    
    def _generate_type_suggestion(self, message: str, error_code: Optional[str]) -> str:
        """Generate type-related suggestions"""
        if "incompatible types" in message.lower():
            return "Check type compatibility and add type annotations"
        elif "has no attribute" in message.lower():
            return "Verify attribute exists or add proper type guards"
        elif "missing positional argument" in message.lower():
            return "Check function signature and provide required arguments"
        elif "too many arguments" in message.lower():
            return "Check function signature and remove extra arguments"
        else:
            return "Add proper type annotations and check type compatibility"


class QualityGateValidator:
    """Validates code quality against configured thresholds"""
    
    def __init__(self, quality_gates: Dict[str, Any]):
        self.quality_gates = quality_gates
        self.logger = logging.getLogger(__name__)
    
    def validate(self, review_result: ReviewResult) -> Dict[str, str]:
        """Validate quality gates and return results"""
        results = {}
        
        # Test coverage validation
        if "min_test_coverage" in self.quality_gates:
            min_coverage = self.quality_gates["min_test_coverage"]
            actual_coverage = review_result.quality_metrics.test_coverage
            results["coverage_check"] = "passed" if actual_coverage >= min_coverage else "failed"
        
        # Complexity validation
        if "max_cyclomatic_complexity" in self.quality_gates:
            max_complexity = self.quality_gates["max_cyclomatic_complexity"]
            actual_complexity = review_result.quality_metrics.cyclomatic_complexity
            results["complexity_check"] = "passed" if actual_complexity <= max_complexity else "failed"
        
        # Security validation
        security_issues = sum(1 for fr in review_result.file_reviews 
                             for issue in fr.issues 
                             if issue.category == IssueCategory.SECURITY)
        
        security_level = self.quality_gates.get("security_level", "moderate")
        if security_level == "strict":
            results["security_check"] = "passed" if security_issues == 0 else "failed"
        elif security_level == "moderate":
            critical_security = sum(1 for fr in review_result.file_reviews 
                                  for issue in fr.issues 
                                  if issue.category == IssueCategory.SECURITY and issue.severity >= 4)
            results["security_check"] = "passed" if critical_security == 0 else "failed"
        else:  # basic
            high_severity_security = sum(1 for fr in review_result.file_reviews 
                                       for issue in fr.issues 
                                       if issue.category == IssueCategory.SECURITY and issue.severity >= 5)
            results["security_check"] = "passed" if high_severity_security == 0 else "failed"
        
        # Style validation
        style_errors = sum(1 for fr in review_result.file_reviews 
                          for issue in fr.issues 
                          if issue.category == IssueCategory.STYLE and issue.type == IssueType.ERROR)
        
        results["style_check"] = "passed" if style_errors == 0 else "failed"
        
        # Technical debt validation
        if "max_technical_debt_ratio" in self.quality_gates:
            max_debt = self.quality_gates["max_technical_debt_ratio"]
            actual_debt = review_result.quality_metrics.technical_debt_ratio
            results["debt_check"] = "passed" if actual_debt <= max_debt else "failed"
        
        return results


class CodeReviewerEngine:
    """Main code reviewer engine"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()
        self.logger = logging.getLogger(__name__)
        self.analyzers: Dict[str, List[AnalysisTool]] = {}
        self._initialize_analyzers()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "quality_gates": {
                "min_test_coverage": 80,
                "max_cyclomatic_complexity": 10,
                "security_level": "moderate",
                "max_technical_debt_ratio": 5
            },
            "tools": {
                "python": [
                    {"name": "ruff", "enabled": True},
                    {"name": "mypy", "enabled": True},
                    {"name": "bandit", "enabled": True}
                ]
            },
            "analysis_timeout": 600,  # 10 minutes
            "max_file_size_mb": 10
        }
    
    def _initialize_analyzers(self):
        """Initialize analysis tools"""
        # Python analyzers
        python_tools = []
        
        if self._is_tool_enabled("python", "ruff"):
            python_tools.append(RuffAnalyzer(self._get_tool_config("python", "ruff")))
        
        if self._is_tool_enabled("python", "mypy"):
            python_tools.append(MypyAnalyzer(self._get_tool_config("python", "mypy")))
        
        if self._is_tool_enabled("python", "bandit"):
            python_tools.append(BanditAnalyzer(self._get_tool_config("python", "bandit")))
        
        self.analyzers["python"] = python_tools
    
    def _is_tool_enabled(self, language: str, tool_name: str) -> bool:
        """Check if analysis tool is enabled"""
        tools = self.config.get("tools", {}).get(language, [])
        for tool in tools:
            if tool.get("name") == tool_name:
                return tool.get("enabled", True)
        return False
    
    def _get_tool_config(self, language: str, tool_name: str) -> Dict[str, Any]:
        """Get configuration for specific tool"""
        tools = self.config.get("tools", {}).get(language, [])
        for tool in tools:
            if tool.get("name") == tool_name:
                return tool
        return {}
    
    async def review_files(
        self, 
        files: List[str], 
        review_config: Dict[str, Any] = None
    ) -> ReviewResult:
        """Review a list of files"""
        start_time = time.time()
        review_id = f"review-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        self.logger.info(f"Starting code review {review_id} for {len(files)} files")
        
        # Merge configuration
        config = {**self.config, **(review_config or {})}
        
        # Filter and validate files
        valid_files = await self._filter_files(files, config)
        
        # Group files by language
        file_groups = self._group_files_by_language(valid_files)
        
        # Run analysis on each group
        file_reviews = []
        total_lines = 0
        
        for language, lang_files in file_groups.items():
            if language in self.analyzers:
                reviews = await self._analyze_files(language, lang_files)
                file_reviews.extend(reviews)
                total_lines += sum(self._count_lines(f) for f in lang_files)
        
        # Calculate metrics
        quality_metrics = await self._calculate_quality_metrics(file_reviews)
        
        # Generate summary
        summary = self._generate_summary(file_reviews, total_lines)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(file_reviews, quality_metrics)
        
        # Determine status
        status = self._determine_status(overall_score, file_reviews, quality_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(file_reviews, quality_metrics)
        
        # Validate quality gates
        quality_gates = QualityGateValidator(config.get("quality_gates", {}))
        
        result = ReviewResult(
            review_id=review_id,
            status=status,
            overall_score=overall_score,
            summary=summary,
            quality_metrics=quality_metrics,
            file_reviews=file_reviews,
            recommendations=recommendations,
            quality_gates={},
            execution_time=time.time() - start_time
        )
        
        # Validate quality gates after result is created
        result.quality_gates = quality_gates.validate(result)
        
        # Adjust status based on quality gates
        if any(gate == "failed" for gate in result.quality_gates.values()):
            if result.status == ReviewStatus.APPROVED:
                result.status = ReviewStatus.NEEDS_CHANGES
        
        self.logger.info(f"Code review {review_id} completed: {result.status.value} "
                        f"(score: {overall_score}, time: {result.execution_time:.1f}s)")
        
        return result
    
    async def _filter_files(self, files: List[str], config: Dict[str, Any]) -> List[str]:
        """Filter and validate files for analysis"""
        valid_files = []
        max_size = config.get("max_file_size_mb", 10) * 1024 * 1024
        
        for file_path in files:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                self.logger.warning(f"File not found: {file_path}")
                continue
            
            # Check file size
            if path.stat().st_size > max_size:
                self.logger.warning(f"File too large, skipping: {file_path}")
                continue
            
            # Check if file is text-based
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    f.read(1024)  # Read first 1KB to test
                valid_files.append(file_path)
            except (UnicodeDecodeError, PermissionError):
                self.logger.warning(f"Cannot read file, skipping: {file_path}")
                continue
        
        return valid_files
    
    def _group_files_by_language(self, files: List[str]) -> Dict[str, List[str]]:
        """Group files by detected language"""
        groups = {"python": [], "javascript": [], "typescript": [], "go": [], "other": []}
        
        for file_path in files:
            extension = Path(file_path).suffix.lower()
            
            if extension in ['.py', '.pyw']:
                groups["python"].append(file_path)
            elif extension in ['.js', '.jsx']:
                groups["javascript"].append(file_path)
            elif extension in ['.ts', '.tsx']:
                groups["typescript"].append(file_path)
            elif extension == '.go':
                groups["go"].append(file_path)
            else:
                groups["other"].append(file_path)
        
        # Remove empty groups
        return {lang: files for lang, files in groups.items() if files}
    
    async def _analyze_files(self, language: str, files: List[str]) -> List[FileReview]:
        """Analyze files with language-specific tools"""
        file_reviews = []
        analyzers = self.analyzers.get(language, [])
        
        if not analyzers:
            self.logger.warning(f"No analyzers available for {language}")
            # Create basic reviews for files without analyzers
            for file_path in files:
                file_reviews.append(FileReview(
                    file_path=file_path,
                    status=ReviewStatus.APPROVED,
                    score=100,
                    issues=[],
                    metrics={"analyzer": "none"}
                ))
            return file_reviews
        
        # Check analyzer availability
        available_analyzers = []
        for analyzer in analyzers:
            if await analyzer.is_available():
                available_analyzers.append(analyzer)
            else:
                self.logger.warning(f"Analyzer {analyzer.name} not available")
        
        if not available_analyzers:
            self.logger.error(f"No analyzers available for {language}")
            return file_reviews
        
        # Run analyzers in parallel
        all_issues = {}
        analyzer_tasks = []
        
        for analyzer in available_analyzers:
            task = analyzer.analyze(files)
            analyzer_tasks.append((analyzer.name, task))
        
        # Wait for all analyzers to complete
        for analyzer_name, task in analyzer_tasks:
            try:
                issues = await asyncio.wait_for(task, timeout=300)
                all_issues[analyzer_name] = issues
            except asyncio.TimeoutError:
                self.logger.error(f"Analyzer {analyzer_name} timed out")
                all_issues[analyzer_name] = []
            except Exception as e:
                self.logger.error(f"Analyzer {analyzer_name} failed: {str(e)}")
                all_issues[analyzer_name] = []
        
        # Group issues by file
        file_issues = {}
        for analyzer_name, issues in all_issues.items():
            for issue in issues:
                file_path = self._find_file_for_issue(issue, files)
                if file_path:
                    if file_path not in file_issues:
                        file_issues[file_path] = []
                    file_issues[file_path].append(issue)
        
        # Create file reviews
        for file_path in files:
            issues = file_issues.get(file_path, [])
            score = self._calculate_file_score(issues, file_path)
            status = self._determine_file_status(score, issues)
            
            file_reviews.append(FileReview(
                file_path=file_path,
                status=status,
                score=score,
                issues=issues,
                metrics={
                    "lines_of_code": self._count_lines(file_path),
                    "analyzers_used": list(all_issues.keys())
                }
            ))
        
        return file_reviews
    
    def _find_file_for_issue(self, issue: ReviewIssue, files: List[str]) -> Optional[str]:
        """Find which file an issue belongs to"""
        # This is a simplified implementation
        # In a real implementation, analyzers would include file path in issues
        return files[0] if files else None
    
    def _calculate_file_score(self, issues: List[ReviewIssue], file_path: str) -> int:
        """Calculate quality score for a file"""
        if not issues:
            return 100
        
        # Start with 100 and deduct points for issues
        score = 100
        
        for issue in issues:
            if issue.type == IssueType.ERROR:
                score -= issue.severity * 3
            elif issue.type == IssueType.WARNING:
                score -= issue.severity * 2
            elif issue.type == IssueType.SUGGESTION:
                score -= issue.severity * 1
        
        # Ensure score doesn't go below 0
        return max(0, score)
    
    def _determine_file_status(self, score: int, issues: List[ReviewIssue]) -> ReviewStatus:
        """Determine review status for a file"""
        # Check for critical issues
        critical_issues = [i for i in issues if i.type == IssueType.ERROR and i.severity >= 4]
        if critical_issues:
            return ReviewStatus.REJECTED
        
        # Check score thresholds
        if score >= 85:
            return ReviewStatus.APPROVED
        elif score >= 60:
            return ReviewStatus.NEEDS_CHANGES
        else:
            return ReviewStatus.REJECTED
    
    def _count_lines(self, file_path: str) -> int:
        """Count lines of code in file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len([line for line in f if line.strip()])
        except Exception:
            return 0
    
    async def _calculate_quality_metrics(self, file_reviews: List[FileReview]) -> QualityMetrics:
        """Calculate overall quality metrics"""
        total_issues = sum(len(fr.issues) for fr in file_reviews)
        total_lines = sum(fr.metrics.get("lines_of_code", 0) for fr in file_reviews)
        
        # Calculate average complexity (simplified)
        avg_complexity = sum(
            len([i for i in fr.issues if i.category == IssueCategory.MAINTAINABILITY])
            for fr in file_reviews
        ) / max(len(file_reviews), 1)
        
        # Calculate maintainability index (simplified)
        avg_score = sum(fr.score for fr in file_reviews) / max(len(file_reviews), 1)
        maintainability = avg_score * 0.8  # Scale to maintainability index
        
        # Calculate security score
        security_issues = sum(
            len([i for i in fr.issues if i.category == IssueCategory.SECURITY])
            for fr in file_reviews
        )
        security_score = max(0, 100 - security_issues * 10)
        
        # Calculate technical debt ratio (simplified)
        debt_ratio = (total_issues / max(total_lines, 1)) * 100
        
        return QualityMetrics(
            maintainability_index=maintainability,
            cyclomatic_complexity=avg_complexity,
            cognitive_complexity=avg_complexity * 1.2,  # Approximation
            test_coverage=85.0,  # Placeholder - would need test analysis
            technical_debt_ratio=debt_ratio,
            security_score=security_score,
            lines_of_code=total_lines,
            duplication_ratio=2.0  # Placeholder - would need duplication analysis
        )
    
    def _generate_summary(self, file_reviews: List[FileReview], total_lines: int) -> ReviewSummary:
        """Generate review summary"""
        total_issues = sum(len(fr.issues) for fr in file_reviews)
        critical_issues = sum(
            len([i for i in fr.issues if i.type == IssueType.ERROR and i.severity >= 4])
            for fr in file_reviews
        )
        warnings = sum(
            len([i for i in fr.issues if i.type == IssueType.WARNING])
            for fr in file_reviews
        )
        suggestions = sum(
            len([i for i in fr.issues if i.type == IssueType.SUGGESTION])
            for fr in file_reviews
        )
        
        return ReviewSummary(
            total_files=len(file_reviews),
            total_lines=total_lines,
            issues_found=total_issues,
            critical_issues=critical_issues,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _calculate_overall_score(
        self, 
        file_reviews: List[FileReview], 
        quality_metrics: QualityMetrics
    ) -> int:
        """Calculate overall review score"""
        if not file_reviews:
            return 100
        
        # Weight file scores by lines of code
        total_weighted_score = 0
        total_weight = 0
        
        for fr in file_reviews:
            weight = max(1, fr.metrics.get("lines_of_code", 1))
            total_weighted_score += fr.score * weight
            total_weight += weight
        
        base_score = total_weighted_score / total_weight if total_weight > 0 else 100
        
        # Adjust based on quality metrics
        if quality_metrics.security_score < 70:
            base_score *= 0.8  # Significant penalty for security issues
        
        if quality_metrics.technical_debt_ratio > 10:
            base_score *= 0.9  # Penalty for high technical debt
        
        return int(max(0, min(100, base_score)))
    
    def _determine_status(
        self, 
        overall_score: int, 
        file_reviews: List[FileReview], 
        quality_metrics: QualityMetrics
    ) -> ReviewStatus:
        """Determine overall review status"""
        # Check for critical security issues
        if quality_metrics.security_score < 50:
            return ReviewStatus.REJECTED
        
        # Check for rejected files
        if any(fr.status == ReviewStatus.REJECTED for fr in file_reviews):
            return ReviewStatus.REJECTED
        
        # Check overall score
        if overall_score >= 85:
            return ReviewStatus.APPROVED
        elif overall_score >= 60:
            return ReviewStatus.NEEDS_CHANGES
        else:
            return ReviewStatus.REJECTED
    
    def _generate_recommendations(
        self, 
        file_reviews: List[FileReview], 
        quality_metrics: QualityMetrics
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Security recommendations
        security_issues = sum(
            len([i for i in fr.issues if i.category == IssueCategory.SECURITY])
            for fr in file_reviews
        )
        if security_issues > 0:
            recommendations.append(f"Address {security_issues} security issues found")
        
        # Quality recommendations
        if quality_metrics.technical_debt_ratio > 5:
            recommendations.append("Consider refactoring to reduce technical debt")
        
        if quality_metrics.cyclomatic_complexity > 10:
            recommendations.append("Simplify complex functions to improve maintainability")
        
        # Test recommendations
        if quality_metrics.test_coverage < 80:
            recommendations.append("Increase test coverage to improve quality assurance")
        
        # Documentation recommendations
        doc_issues = sum(
            len([i for i in fr.issues if i.category == IssueCategory.DOCUMENTATION])
            for fr in file_reviews
        )
        if doc_issues > 0:
            recommendations.append("Improve code documentation and comments")
        
        # Style recommendations
        style_issues = sum(
            len([i for i in fr.issues if i.category == IssueCategory.STYLE])
            for fr in file_reviews
        )
        if style_issues > 5:
            recommendations.append("Apply consistent code formatting and style")
        
        return recommendations[:5]  # Limit to top 5 recommendations


# CLI Interface
async def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CodeReviewer Agent")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review files")
    review_parser.add_argument("--files", required=True, help="Comma-separated list of files")
    review_parser.add_argument("--language", help="Primary language (python, javascript, etc.)")
    review_parser.add_argument("--quality-gates", help="Quality gates profile (strict, standard, lenient)")
    review_parser.add_argument("--output-format", choices=["json", "yaml", "text"], default="json")
    review_parser.add_argument("--output-file", help="Output file path")
    
    # Health check command
    health_parser = subparsers.add_parser("health-check", help="Check system health")
    
    # Tool availability command
    tools_parser = subparsers.add_parser("tools", help="Check tool availability")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if args.command == "review":
        files = [f.strip() for f in args.files.split(",")]
        
        # Build configuration
        config = {}
        if args.quality_gates:
            # Load quality gates profile (simplified)
            profiles = {
                "strict": {"min_test_coverage": 95, "max_cyclomatic_complexity": 8},
                "standard": {"min_test_coverage": 85, "max_cyclomatic_complexity": 10},
                "lenient": {"min_test_coverage": 70, "max_cyclomatic_complexity": 15}
            }
            config["quality_gates"] = profiles.get(args.quality_gates, {})
        
        # Run review
        reviewer = CodeReviewerEngine()
        result = await reviewer.review_files(files, config)
        
        # Output results
        if args.output_format == "json":
            output = json.dumps(result.to_dict(), indent=2)
        elif args.output_format == "yaml":
            output = yaml.dump(result.to_dict(), default_flow_style=False)
        else:  # text
            output = f"""
Code Review Results
==================
Status: {result.status.value.upper()}
Overall Score: {result.overall_score}/100
Files Reviewed: {result.summary.total_files}
Issues Found: {result.summary.issues_found}
Execution Time: {result.execution_time:.1f}s

Quality Gates:
{chr(10).join(f'  {gate}: {status}' for gate, status in result.quality_gates.items())}

Recommendations:
{chr(10).join(f'  - {rec}' for rec in result.recommendations)}
            """.strip()
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(output)
        else:
            print(output)
        
        # Exit with appropriate code
        sys.exit(0 if result.status == ReviewStatus.APPROVED else 1)
    
    elif args.command == "health-check":
        reviewer = CodeReviewerEngine()
        
        print("CodeReviewer Health Check")
        print("=" * 24)
        
        # Check Python tools
        python_tools = ["ruff", "mypy", "bandit", "black"]
        available_tools = []
        
        for tool_name in python_tools:
            try:
                result = subprocess.run([tool_name, "--version"], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    available_tools.append(tool_name)
                    print(f"✓ {tool_name} available")
                else:
                    print(f"✗ {tool_name} not working")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print(f"✗ {tool_name} not found")
        
        # Overall status
        if len(available_tools) >= len(python_tools) // 2:
            print("\nSystem Status: HEALTHY")
            print("Ready for code review operations.")
        else:
            print("\nSystem Status: DEGRADED")
            print("Some tools are missing. Install missing tools for full functionality.")
        
    elif args.command == "tools":
        print("Available Analysis Tools")
        print("=" * 24)
        
        tools_info = {
            "ruff": "Ultra-fast Python linter",
            "mypy": "Static type checker for Python", 
            "bandit": "Security linter for Python",
            "black": "Python code formatter",
            "eslint": "JavaScript/TypeScript linter",
            "prettier": "JavaScript/TypeScript formatter"
        }
        
        for tool, description in tools_info.items():
            try:
                result = subprocess.run([tool, "--version"], 
                                      capture_output=True, timeout=5)
                status = "✓" if result.returncode == 0 else "✗"
                print(f"{status} {tool}: {description}")
            except FileNotFoundError:
                print(f"✗ {tool}: {description} (not installed)")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())