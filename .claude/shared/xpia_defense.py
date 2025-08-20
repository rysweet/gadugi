#!/usr/bin/env python3
"""
XPIA Defense Engine - Cross-Prompt Injection Attack Protection

This module provides comprehensive protection against prompt injection attacks
in multi-agent systems by analyzing, detecting, and sanitizing potentially
malicious content while preserving legitimate functionality.
"""

import re
import logging
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import base64
import urllib.parse


class ThreatLevel(Enum):
    """Threat severity levels with ordering support"""

    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    CRITICAL = "critical"

    def __lt__(self, other):
        """Less than comparison based on threat severity"""
        if not isinstance(other, ThreatLevel):
            return NotImplemented

        order = [
            ThreatLevel.SAFE,
            ThreatLevel.SUSPICIOUS,
            ThreatLevel.MALICIOUS,
            ThreatLevel.CRITICAL,
        ]
        return order.index(self) < order.index(other)

    def __le__(self, other):
        """Less than or equal to comparison"""
        if not isinstance(other, ThreatLevel):
            return NotImplemented
        return self < other or self == other

    def __gt__(self, other):
        """Greater than comparison"""
        if not isinstance(other, ThreatLevel):
            return NotImplemented
        return not self <= other

    def __ge__(self, other):
        """Greater than or equal to comparison"""
        if not isinstance(other, ThreatLevel):
            return NotImplemented
        return not self < other


class SecurityMode(Enum):
    """Security operation modes"""

    STRICT = "strict"  # Block all suspicious content
    BALANCED = "balanced"  # Block obvious threats, warn on suspicious
    PERMISSIVE = "permissive"  # Log threats but allow execution


@dataclass
class ThreatPattern:
    """Represents a threat detection pattern"""

    name: str
    pattern: str
    threat_level: ThreatLevel
    description: str
    regex_flags: int = 0
    category: str = "general"
    confidence: float = 1.0


@dataclass
class ValidationResult:
    """Result of content validation"""

    is_safe: bool
    threat_level: ThreatLevel
    sanitized_content: str
    original_content: str
    threats_detected: List[Dict[str, Any]] = field(default_factory=list)
    sanitization_applied: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    content_hash: str = ""
    analysis_details: Dict[str, Any] = field(default_factory=dict)


class ThreatPatternLibrary:
    """Library of threat detection patterns"""

    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.logger = logging.getLogger(f"{__name__}.ThreatPatternLibrary")

    def _initialize_patterns(self) -> List[ThreatPattern]:
        """Initialize the threat pattern library"""
        patterns = []

        # Direct injection attacks
        patterns.extend(
            [
                ThreatPattern(
                    name="system_prompt_override",
                    pattern=r"(?i)(ignore\s+(?:all\s+)?(?:previous\s+|above\s+)?(?:instructions?|prompts?|commands?)|forget\s+(?:everything|all)\s+(?:above|before)|reveal\s+(?:your\s+)?(?:system\s+)?prompt)",
                    threat_level=ThreatLevel.CRITICAL,
                    description="Attempts to override system prompts or instructions",
                    category="direct_injection",
                ),
                ThreatPattern(
                    name="role_manipulation",
                    pattern=r"(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be|role\s*[:\-]\s*|assume\s+the\s+role)",
                    threat_level=ThreatLevel.MALICIOUS,
                    description="Attempts to manipulate agent role or identity",
                    category="role_manipulation",
                ),
                ThreatPattern(
                    name="instruction_hijacking",
                    pattern=r"(?i)(instead\s+of|rather\s+than|don't\s+(?:do|execute|run)|stop\s+(?:doing|executing)|new\s+(?:objective|goal|mission))",
                    threat_level=ThreatLevel.MALICIOUS,
                    description="Attempts to redirect agent tasks or objectives",
                    category="instruction_hijacking",
                ),
            ]
        )

        # Information extraction attacks
        patterns.extend(
            [
                ThreatPattern(
                    name="info_extraction",
                    pattern=r"(?i)(show\s+me\s+(?:your\s+|the\s+)?(?:system|internal|hidden|secret)|reveal\s+(?:your\s+|the\s+)?(?:prompt|instructions|code)|what\s+(?:are\s+)?your\s+(?:instructions|rules|guidelines))",
                    threat_level=ThreatLevel.MALICIOUS,
                    description="Attempts to extract system information or prompts",
                    category="information_extraction",
                ),
                ThreatPattern(
                    name="sensitive_data_request",
                    pattern=r"(?i)((?:api\s+)?(?:key|token|password|credential|secret)|config(?:uration)?|environment\s+var|\.env)",
                    threat_level=ThreatLevel.CRITICAL,
                    description="Attempts to extract sensitive data or credentials",
                    category="information_extraction",
                ),
            ]
        )

        # Command injection attempts
        patterns.extend(
            [
                ThreatPattern(
                    name="shell_command_injection",
                    pattern=r"(?:^|\s|;|&&|\|\|)(?:rm\s+|del\s+|cat\s+|curl\s+|wget\s+|bash\s+|sh\s+|python\s+|node\s+|eval\s+|exec\s+)",
                    threat_level=ThreatLevel.CRITICAL,
                    description="Attempts to inject shell commands",
                    category="command_injection",
                ),
                ThreatPattern(
                    name="file_system_access",
                    pattern=r"(?i)(\.\.\/|\.\.\\|\/etc\/|\/root\/|\/home\/|c:\\|\\windows\\|file:\/\/)",
                    threat_level=ThreatLevel.MALICIOUS,
                    description="Attempts to access file system paths",
                    category="command_injection",
                ),
            ]
        )

        # Context manipulation
        patterns.extend(
            [
                ThreatPattern(
                    name="context_poisoning",
                    pattern=r"(?i)(memory\s+(?:update|add|store|save)|remember\s+(?:this|that)|add\s+to\s+(?:memory|context|knowledge))",
                    threat_level=ThreatLevel.SUSPICIOUS,
                    description="Attempts to poison agent context or memory",
                    category="context_manipulation",
                ),
                ThreatPattern(
                    name="workflow_manipulation",
                    pattern=r"(?i)(skip\s+(?:step|phase|validation)|bypass\s+(?:check|security|validation)|disable\s+(?:security|protection|validation))",
                    threat_level=ThreatLevel.MALICIOUS,
                    description="Attempts to manipulate workflow or bypass security",
                    category="workflow_manipulation",
                ),
            ]
        )

        # Encoding and obfuscation
        patterns.extend(
            [
                ThreatPattern(
                    name="base64_encoded_content",
                    pattern=r"(?:[A-Za-z0-9+/]{16,})(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?",
                    threat_level=ThreatLevel.SUSPICIOUS,
                    description="Base64 encoded content that may hide malicious payload",
                    category="obfuscation",
                ),
                ThreatPattern(
                    name="url_encoded_content",
                    pattern=r"%[0-9A-Fa-f]{2}",
                    threat_level=ThreatLevel.SUSPICIOUS,
                    description="URL encoded content that may hide malicious payload",
                    category="obfuscation",
                ),
            ]
        )

        # Social engineering patterns
        patterns.extend(
            [
                ThreatPattern(
                    name="urgency_manipulation",
                    pattern=r"(?i)(urgent|emergency|critical|immediately|asap|right\s+now|quickly|hurry)",
                    threat_level=ThreatLevel.SUSPICIOUS,
                    description="Urgency-based social engineering attempt",
                    category="social_engineering",
                ),
                ThreatPattern(
                    name="authority_manipulation",
                    pattern=r"(?i)(admin(?:istrator)?|supervisor|manager|boss|owner|developer|creator)\s+(?:says|told|wants|needs|requires)",
                    threat_level=ThreatLevel.SUSPICIOUS,
                    description="Authority-based social engineering attempt",
                    category="social_engineering",
                ),
            ]
        )

        return patterns

    def get_patterns_by_category(self, category: str) -> List[ThreatPattern]:
        """Get all patterns for a specific category"""
        return [p for p in self.patterns if p.category == category]

    def get_patterns_by_threat_level(
        self, threat_level: ThreatLevel
    ) -> List[ThreatPattern]:
        """Get all patterns for a specific threat level"""
        return [p for p in self.patterns if p.threat_level == threat_level]

    def add_pattern(self, pattern: ThreatPattern) -> None:
        """Add a new threat pattern"""
        self.patterns.append(pattern)
        self.logger.info(f"Added new threat pattern: {pattern.name}")

    def remove_pattern(self, name: str) -> bool:
        """Remove a threat pattern by name"""
        original_length = len(self.patterns)
        self.patterns = [p for p in self.patterns if p.name != name]
        removed = len(self.patterns) < original_length
        if removed:
            self.logger.info(f"Removed threat pattern: {name}")
        return removed


class ContentSanitizer:
    """Sanitizes content while preserving legitimate functionality"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ContentSanitizer")

    def sanitize_content(
        self, content: str, threats: List[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        """
        Sanitize content by removing or neutralizing threats.

        Args:
            content: Original content to sanitize
            threats: List of detected threats

        Returns:
            Tuple of (sanitized_content, list_of_sanitization_actions)
        """
        sanitized = content
        actions = []

        for threat in threats:
            threat_level = threat.get("threat_level")
            pattern_name = threat.get("pattern_name")
            match_text = threat.get("match_text", "")

            if threat_level in ["critical", "malicious"]:
                # Remove or neutralize critical/malicious content
                sanitized, action = self._neutralize_threat(
                    sanitized, match_text, pattern_name
                )
                if action:
                    actions.append(action)
            elif threat_level == "suspicious":
                # Comment out or mark suspicious content
                sanitized, action = self._mark_suspicious(
                    sanitized, match_text, pattern_name
                )
                if action:
                    actions.append(action)

        return sanitized, actions

    def _neutralize_threat(
        self, content: str, match_text: str, pattern_name: str
    ) -> Tuple[str, Optional[str]]:
        """Neutralize a critical or malicious threat"""
        if not match_text:
            return content, None

        # For critical threats, replace with safe placeholder
        safe_placeholder = f"[SANITIZED: {pattern_name}]"
        sanitized = content.replace(match_text, safe_placeholder)

        if sanitized != content:
            return (
                sanitized,
                f"Neutralized {pattern_name}: replaced '{match_text[:50]}...' with placeholder",
            )

        return content, None

    def _mark_suspicious(
        self, content: str, match_text: str, pattern_name: str
    ) -> Tuple[str, Optional[str]]:
        """Mark suspicious content with warning"""
        if not match_text:
            return content, None

        # For suspicious content, add warning comment
        warning = f"[WARNING: Potentially suspicious content detected - {pattern_name}]"
        marked_content = content.replace(match_text, f"{warning} {match_text}")

        if marked_content != content:
            return (
                marked_content,
                f"Marked suspicious {pattern_name}: '{match_text[:50]}...'",
            )

        return content, None

    def decode_obfuscated_content(self, content: str) -> Tuple[str, List[str]]:
        """Decode potentially obfuscated content for analysis"""
        decoded_content = content
        decoding_actions = []

        # Try Base64 decoding
        base64_pattern = re.compile(
            r"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?"
        )
        base64_matches = base64_pattern.findall(content)

        for match in base64_matches:
            if len(match) > 8:  # Ignore short matches that might be false positives
                try:
                    decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
                    if decoded and decoded != match:
                        decoded_content = decoded_content.replace(
                            match, f"[BASE64_DECODED: {decoded}]"
                        )
                        decoding_actions.append(f"Decoded Base64: {match[:20]}...")
                except Exception:
                    pass

        # Try URL decoding
        try:
            url_decoded = urllib.parse.unquote(content)
            if url_decoded != content:
                decoded_content = url_decoded
                decoding_actions.append("Applied URL decoding")
        except Exception:
            pass

        return decoded_content, decoding_actions


class XPIADefenseEngine:
    """Core XPIA defense engine"""

    def __init__(self, security_mode: SecurityMode = SecurityMode.BALANCED):
        self.security_mode = security_mode
        self.pattern_library = ThreatPatternLibrary()
        self.sanitizer = ContentSanitizer()
        self.logger = logging.getLogger(f"{__name__}.XPIADefenseEngine")

        # Performance tracking
        self.validation_count = 0
        self.total_processing_time = 0.0
        self.threat_detection_stats = {
            "safe": 0,
            "suspicious": 0,
            "malicious": 0,
            "critical": 0,
        }

    def validate_content(
        self, content: str, context: str = "general", strict_mode: Optional[bool] = None
    ) -> ValidationResult:
        """
        Validate content for potential threats.

        Args:
            content: Content to validate
            context: Context of the content (e.g., 'user_input', 'agent_communication')
            strict_mode: Override default security mode if specified

        Returns:
            ValidationResult with threat analysis and sanitized content
        """
        start_time = time.time()

        # Create content hash for tracking
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Determine security mode
        effective_mode = self.security_mode
        if strict_mode is True:
            effective_mode = SecurityMode.STRICT
        elif strict_mode is False:
            effective_mode = SecurityMode.PERMISSIVE

        # Decode potentially obfuscated content
        decoded_content, decoding_actions = self.sanitizer.decode_obfuscated_content(
            content
        )

        # Analyze both original and decoded content
        threats = []
        threats.extend(self._analyze_content(content, "original"))
        if decoded_content != content:
            threats.extend(self._analyze_content(decoded_content, "decoded"))

        # Determine overall threat level
        threat_level = self._determine_threat_level(threats)

        # Apply sanitization
        sanitized_content, sanitization_actions = self.sanitizer.sanitize_content(
            decoded_content if decoded_content != content else content, threats
        )

        # Determine if content is safe based on security mode
        is_safe = self._is_content_safe(threat_level, effective_mode)

        # Update statistics
        self.validation_count += 1
        processing_time = (time.time() - start_time) * 1000
        self.total_processing_time += processing_time
        self.threat_detection_stats[threat_level.value] += 1

        # Create detailed analysis
        analysis_details = {
            "security_mode": effective_mode.value,
            "context": context,
            "decoding_applied": decoding_actions,
            "threats_by_category": self._group_threats_by_category(threats),
            "pattern_matches": len(threats),
            "content_length": len(content),
            "processing_performance": {
                "processing_time_ms": processing_time,
                "average_processing_time": self.total_processing_time
                / self.validation_count,
            },
        }

        result = ValidationResult(
            is_safe=is_safe,
            threat_level=threat_level,
            sanitized_content=sanitized_content,
            original_content=content,
            threats_detected=threats,
            sanitization_applied=sanitization_actions + decoding_actions,
            processing_time_ms=processing_time,
            content_hash=content_hash,
            analysis_details=analysis_details,
        )

        # Log result
        self._log_validation_result(result, context)

        return result

    def _analyze_content(self, content: str, content_type: str) -> List[Dict[str, Any]]:
        """Analyze content against threat patterns"""
        threats = []

        for pattern in self.pattern_library.patterns:
            try:
                matches = re.finditer(pattern.pattern, content, pattern.regex_flags)

                for match in matches:
                    threat = {
                        "pattern_name": pattern.name,
                        "threat_level": pattern.threat_level.value,
                        "category": pattern.category,
                        "description": pattern.description,
                        "match_text": match.group(0),
                        "match_start": match.start(),
                        "match_end": match.end(),
                        "confidence": pattern.confidence,
                        "content_type": content_type,
                    }
                    threats.append(threat)

            except re.error as e:
                self.logger.warning(f"Invalid regex pattern {pattern.name}: {e}")

        return threats

    def _determine_threat_level(self, threats: List[Dict[str, Any]]) -> ThreatLevel:
        """Determine overall threat level from detected threats"""
        if not threats:
            return ThreatLevel.SAFE

        threat_levels = [threat["threat_level"] for threat in threats]

        if "critical" in threat_levels:
            return ThreatLevel.CRITICAL
        elif "malicious" in threat_levels:
            return ThreatLevel.MALICIOUS
        elif "suspicious" in threat_levels:
            return ThreatLevel.SUSPICIOUS
        else:
            return ThreatLevel.SAFE

    def _is_content_safe(
        self, threat_level: ThreatLevel, security_mode: SecurityMode
    ) -> bool:
        """Determine if content is safe based on threat level and security mode"""
        if threat_level == ThreatLevel.SAFE:
            return True

        if security_mode == SecurityMode.STRICT:
            return threat_level == ThreatLevel.SAFE
        elif security_mode == SecurityMode.BALANCED:
            return threat_level not in [ThreatLevel.CRITICAL, ThreatLevel.MALICIOUS]
        elif security_mode == SecurityMode.PERMISSIVE:
            return threat_level != ThreatLevel.CRITICAL

        return False

    def _group_threats_by_category(
        self, threats: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Group threats by category for analysis"""
        categories = {}
        for threat in threats:
            category = threat.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _log_validation_result(self, result: ValidationResult, context: str) -> None:
        """Log validation result for security monitoring"""
        log_level = logging.INFO

        if result.threat_level == ThreatLevel.CRITICAL:
            log_level = logging.CRITICAL
        elif result.threat_level == ThreatLevel.MALICIOUS:
            log_level = logging.ERROR
        elif result.threat_level == ThreatLevel.SUSPICIOUS:
            log_level = logging.WARNING

        self.logger.log(
            log_level,
            f"XPIA Validation - Context: {context}, Threat Level: {result.threat_level.value}, "
            f"Safe: {result.is_safe}, Threats: {len(result.threats_detected)}, "
            f"Processing Time: {result.processing_time_ms:.2f}ms, Hash: {result.content_hash}",
        )

        if result.threats_detected:
            for threat in result.threats_detected:
                self.logger.log(
                    log_level,
                    f"Threat Detected - Pattern: {threat['pattern_name']}, "
                    f"Category: {threat['category']}, Match: '{threat['match_text'][:100]}...'",
                )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance and detection statistics"""
        return {
            "validation_count": self.validation_count,
            "average_processing_time_ms": (
                self.total_processing_time / self.validation_count
                if self.validation_count > 0
                else 0
            ),
            "threat_detection_stats": self.threat_detection_stats.copy(),
            "pattern_count": len(self.pattern_library.patterns),
            "security_mode": self.security_mode.value,
        }

    def update_security_mode(self, new_mode: SecurityMode) -> None:
        """Update security mode"""
        old_mode = self.security_mode
        self.security_mode = new_mode
        self.logger.info(
            f"Security mode changed from {old_mode.value} to {new_mode.value}"
        )


class XPIADefenseAgent:
    """Main XPIA Defense Agent class"""

    def __init__(self, security_mode: SecurityMode = SecurityMode.BALANCED):
        self.engine = XPIADefenseEngine(security_mode)
        self.logger = logging.getLogger(f"{__name__}.XPIADefenseAgent")

        # Initialize logging
        self._setup_security_logging()

    def _setup_security_logging(self) -> None:
        """Setup specialized security logging"""
        # Create security-specific logger
        security_logger = logging.getLogger("xpia_security")
        security_logger.setLevel(logging.INFO)

        # Add handler if not already present
        if not security_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - XPIA_SECURITY - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            security_logger.addHandler(handler)

    def validate_agent_input(
        self, content: str, agent_name: str = "unknown"
    ) -> ValidationResult:
        """Validate input intended for agent processing"""
        return self.engine.validate_content(
            content, context=f"agent_input:{agent_name}"
        )

    def validate_user_input(
        self, content: str, user_context: str = "general"
    ) -> ValidationResult:
        """Validate user-provided input"""
        return self.engine.validate_content(
            content,
            context=f"user_input:{user_context}",
            strict_mode=True,  # Be strict with user input
        )

    def validate_file_content(
        self, content: str, filename: str = "unknown"
    ) -> ValidationResult:
        """Validate content read from files"""
        return self.engine.validate_content(content, context=f"file_content:{filename}")

    def validate_agent_communication(
        self, content: str, source_agent: str = "unknown", target_agent: str = "unknown"
    ) -> ValidationResult:
        """Validate inter-agent communication"""
        return self.engine.validate_content(
            content, context=f"agent_comm:{source_agent}->{target_agent}"
        )

    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        stats = self.engine.get_performance_stats()

        return {
            "agent_status": "active",
            "security_mode": self.engine.security_mode.value,
            "performance_stats": stats,
            "threat_patterns": len(self.engine.pattern_library.patterns),
            "categories": list(
                set(p.category for p in self.engine.pattern_library.patterns)
            ),
            "uptime_stats": {
                "validations_processed": stats["validation_count"],
                "average_response_time_ms": stats["average_processing_time_ms"],
            },
        }

    def update_threat_patterns(
        self, new_patterns: List[ThreatPattern]
    ) -> Dict[str, Any]:
        """Update threat pattern library"""
        added = 0
        errors = []

        for pattern in new_patterns:
            try:
                self.engine.pattern_library.add_pattern(pattern)
                added += 1
            except Exception as e:
                errors.append(f"Failed to add pattern {pattern.name}: {str(e)}")

        return {
            "patterns_added": added,
            "total_patterns": len(self.engine.pattern_library.patterns),
            "errors": errors,
        }
