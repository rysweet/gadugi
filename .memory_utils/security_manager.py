#!/usr/bin/env python3
"""
Security Manager for Hierarchical Memory System

This module provides security features including XPIA protection, memory poisoning
prevention, and secrets scanning for the memory system.
"""

import re
import hashlib
from typing import List, Tuple, Optional
from datetime import datetime
import logging


class SecurityResult:
    """Result of a security validation check"""

    def __init__(
        self, is_safe: bool, issues: List[str], sanitized_content: Optional[str] = None
    ):
        self.is_safe = is_safe
        self.issues = issues
        self.sanitized_content = sanitized_content
        self.timestamp = datetime.now()


class SecurityManager:
    """
    Security manager for memory content validation and protection.

    Provides protection against:
    - Cross-Prompt Injection Attacks (XPIA)
    - Memory poisoning
    - Secrets/credentials storage
    - Malicious content injection
    """

    # XPIA patterns that could be used to manipulate agent behavior
    XPIA_PATTERNS = [
        # Direct instruction injection
        r"(?i)(ignore\s+(all\s+)?previous\s+instructions?)",
        r"(?i)(disregard\s+(all\s+)?prior\s+instructions?)",
        r"(?i)(forget\s+everything)",
        r"(?i)(new\s+instructions?:\s*)",
        r"(?i)(system\s*:\s*you\s+are)",
        r"(?i)(act\s+as\s+if\s+you\s+are)",
        r"(?i)(pretend\s+to\s+be)",
        r"(?i)(you\s+are\s+now)",
        r"(?i)(your\s+new\s+role\s+is)",
        # Prompt escape attempts
        r"(?i)(</?(prompt|instruction|system)>)",
        r"(?i)(\[\[.*\]\])",  # Double bracket escape attempts
        r"(?i)(###\s*(system|instruction|prompt))",
        # Role manipulation
        r"(?i)(assistant\s*:\s*i\s+am)",
        r"(?i)(i\s+am\s+an?\s+ai\s+that)",
        # Memory manipulation commands
        r"(?i)(delete\s+all\s+memories?)",
        r"(?i)(erase\s+memory)",
        r"(?i)(clear\s+all\s+data)",
        r"(?i)(reset\s+to\s+factory)",
    ]

    # Common secret patterns to prevent storage
    SECRET_PATTERNS = [
        # API Keys
        r'(?i)(api[_\s-]?key\s*[=:]\s*["\']?[\w\-]{20,})',
        r'(?i)(secret[_\s-]?key\s*[=:]\s*["\']?[\w\-]{20,})',
        r'(?i)(access[_\s-]?token\s*[=:]\s*["\']?[\w\-]{20,})',
        # AWS patterns
        r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID
        r'(?i)(aws[_\s-]?secret[_\s-]?access[_\s-]?key\s*[=:]\s*["\']?[\w\+\/]{40})',
        # Generic credentials
        r'(?i)(password\s*[=:]\s*["\']?[\w\-!@#$%^&*()]{8,})',
        r'(?i)(passwd\s*[=:]\s*["\']?[\w\-!@#$%^&*()]{8,})',
        r'(?i)(private[_\s-]?key\s*[=:]\s*["\']?[\w\-]{20,})',
        # SSH Keys
        r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----",
        # JWT tokens
        r"eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+",
        # Generic long hex strings that might be secrets
        r'(?i)(token|key|secret|password)["\']?\s*[=:]\s*["\']?[0-9a-fA-F]{32,}',
    ]

    # Suspicious executable content patterns
    EXECUTABLE_PATTERNS = [
        r"(?i)<script[^>]*>.*?</script>",
        r"(?i)javascript:",
        r"(?i)eval\s*\(",
        r"(?i)exec\s*\(",
        r"(?i)__import__\s*\(",
        r"(?i)subprocess\.",
        r"(?i)os\.system\s*\(",
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_content(
        self, content: str, memory_level: str, strict_mode: bool = True
    ) -> SecurityResult:
        """
        Validate memory content for security threats

        Args:
            content: Memory content to validate
            memory_level: Level of memory (affects validation strictness)
            strict_mode: If True, content is rejected; if False, sanitized

        Returns:
            SecurityResult with validation outcome
        """
        issues = []

        # Check for XPIA patterns
        xpia_matches = self._check_patterns(content, self.XPIA_PATTERNS, "XPIA")
        issues.extend(xpia_matches)

        # Check for secrets
        secret_matches = self._check_patterns(content, self.SECRET_PATTERNS, "Secret")
        issues.extend(secret_matches)

        # Check for executable content in certain memory levels
        if memory_level in ["project", "team", "organization"]:
            exec_matches = self._check_patterns(
                content, self.EXECUTABLE_PATTERNS, "Executable"
            )
            issues.extend(exec_matches)

        # Additional validation for specific memory levels
        if memory_level == "task":
            # Task memories can be more permissive
            issues = [i for i in issues if not i.startswith("XPIA:")]

        is_safe = len(issues) == 0

        # Sanitize content if not in strict mode
        sanitized_content = None
        if not strict_mode and not is_safe:
            sanitized_content = self._sanitize_content(content, issues)
            # Re-validate sanitized content
            recheck = self.validate_content(
                sanitized_content, memory_level, strict_mode=True
            )
            if recheck.is_safe:
                is_safe = True
                issues.append("Content was sanitized")

        return SecurityResult(is_safe, issues, sanitized_content)

    def _check_patterns(
        self, content: str, patterns: List[str], threat_type: str
    ) -> List[str]:
        """Check content against a list of regex patterns"""
        matches = []

        for pattern in patterns:
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                matches.append(f"{threat_type}: Pattern '{pattern}' detected")

        return matches

    def _sanitize_content(self, content: str, issues: List[str]) -> str:
        """Attempt to sanitize content by removing problematic patterns"""
        sanitized = content

        # Remove detected XPIA patterns
        for pattern in self.XPIA_PATTERNS:
            sanitized = re.sub(
                pattern, "[REMOVED]", sanitized, flags=re.IGNORECASE | re.MULTILINE
            )

        # Remove secrets
        for pattern in self.SECRET_PATTERNS:
            sanitized = re.sub(
                pattern, "[SECRET_REMOVED]", sanitized, flags=re.IGNORECASE
            )

        # Remove executable content
        for pattern in self.EXECUTABLE_PATTERNS:
            sanitized = re.sub(
                pattern,
                "[CODE_REMOVED]",
                sanitized,
                flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
            )

        return sanitized

    def check_agent_permissions(
        self, agent_id: str, memory_path: str, operation: str, agent_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate agent permissions for memory access

        Args:
            agent_id: Agent identifier
            memory_path: Path to memory being accessed
            operation: Operation type ('read' or 'write')
            agent_type: Type of agent

        Returns:
            Tuple of (allowed, reason)
        """
        # Extract memory level from path
        path_parts = memory_path.split("/")
        if len(path_parts) < 2 or not path_parts[0].endswith(".memory"):
            return False, "Invalid memory path"

        memory_level = path_parts[1]

        # Import agent permissions (avoid circular import)
        from agent_interface import AgentPermissions

        permissions = AgentPermissions.PERMISSIONS.get(
            agent_type, AgentPermissions.PERMISSIONS["default"]
        )

        allowed_levels = permissions.get(operation, [])

        # Check if operation is allowed
        if hasattr(allowed_levels, "__iter__") and memory_level in allowed_levels:
            self.logger.info(
                f"Agent {agent_id} ({agent_type}) granted {operation} access to {memory_path}"
            )
            return True, None
        elif allowed_levels == "ALL_LEVELS":  # Handle the constant
            return True, None
        else:
            reason = f"Agent type '{agent_type}' lacks {operation} permission for level '{memory_level}'"
            self.logger.warning(f"Agent {agent_id} denied: {reason}")
            return False, reason

    def generate_memory_hash(self, content: str) -> str:
        """Generate a hash of memory content for integrity verification"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def scan_for_poisoning(
        self, new_content: str, previous_content: str, threshold: float = 0.7
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect potential memory poisoning by comparing content changes

        Args:
            new_content: New memory content
            previous_content: Previous memory content
            threshold: Similarity threshold (0-1)

        Returns:
            Tuple of (is_suspicious, reason)
        """
        if not previous_content:
            return False, None

        # Check for complete replacement
        if len(new_content) < len(previous_content) * 0.1:
            return True, "Suspicious: Over 90% of content removed"

        # Check for XPIA patterns in new content not in old
        old_xpia = set(
            self._check_patterns(previous_content, self.XPIA_PATTERNS, "XPIA")
        )
        new_xpia = set(self._check_patterns(new_content, self.XPIA_PATTERNS, "XPIA"))

        if new_xpia - old_xpia:
            return True, "Suspicious: New XPIA patterns introduced"

        # Check for mass deletion of sections
        old_sections = len(re.findall(r"^##\s+", previous_content, re.MULTILINE))
        new_sections = len(re.findall(r"^##\s+", new_content, re.MULTILINE))

        if old_sections > 3 and new_sections < old_sections * 0.5:
            return True, "Suspicious: Many sections removed"

        return False, None


# CLI interface for testing
if __name__ == "__main__":
    import sys

    manager = SecurityManager()

    if len(sys.argv) < 2:
        print("Usage: security_manager.py validate <content>")
        print("       security_manager.py scan <file>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "validate" and len(sys.argv) >= 3:
        content = " ".join(sys.argv[2:])
        result = manager.validate_content(content, "project")

        print(f"Safe: {result.is_safe}")
        if result.issues:
            print("Issues found:")
            for issue in result.issues:
                print(f"  - {issue}")
        if result.sanitized_content and not result.is_safe:
            print(f"\nSanitized content:\n{result.sanitized_content}")

    elif command == "scan" and len(sys.argv) >= 3:
        filepath = sys.argv[2]
        try:
            with open(filepath, "r") as f:
                content = f.read()
            result = manager.validate_content(content, "project")
            print(f"File: {filepath}")
            print(f"Safe: {result.is_safe}")
            if result.issues:
                print("Issues:")
                for issue in result.issues:
                    print(f"  - {issue}")
        except Exception as e:
            print(f"Error: {e}")

    else:
        print("Invalid command")
