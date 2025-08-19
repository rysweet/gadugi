from typing import Any, Dict, Optional

import logging
import time
import sys

#!/usr/bin/env python3
"""
XPIA Defense Middleware - Integration with agent-manager hook system

This module provides transparent XPIA defense integration through the
agent-manager hook system, protecting all agent communications without
requiring changes to existing agent code.
"""

from pathlib import Path

# Add shared modules to path
shared_path = Path(__file__).parent
sys.path.insert(0, str(shared_path))

from xpia_defense import XPIADefenseAgent, SecurityMode, ValidationResult

class XPIAMiddleware:
    """
    XPIA Defense middleware for transparent agent protection.

    Integrates with agent-manager hook system to provide automatic
    threat detection and content sanitization for all agent operations.
    """

    def __init__(self, security_mode: SecurityMode = SecurityMode.BALANCED):
        self.defense_agent = XPIADefenseAgent(security_mode)
        self.logger = logging.getLogger(f"{__name__}.XPIAMiddleware")

        # Configuration
        self.config = {
            "enabled": True,
            "strict_user_input": True,
            "log_all_validations": False,
            "block_on_critical": True,
            "warn_on_suspicious": True,
            "performance_monitoring": True,
        }

        # Statistics
        self.stats = {
            "total_validations": 0,
            "threats_blocked": 0,
            "threats_warned": 0,
            "average_latency_ms": 0.0,
            "total_processing_time_ms": 0.0,
        }

        # Initialize security logging
        self._setup_security_logging()

    def _setup_security_logging(self) -> None:
        """Setup specialized security logging for middleware"""
        security_logger = logging.getLogger("xpia_middleware_security")
        security_logger.setLevel(logging.INFO)

        if not security_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - XPIA_MIDDLEWARE - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            security_logger.addHandler(handler)

    def validate_user_input(
        self, content: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate user input through XPIA defense.

        Args:
            content: User input content to validate
            context: Additional context about the input

        Returns:
            Dictionary with validation results and processed content
        """
        if not self.config["enabled"]:
            return {
                "safe": True,
                "content": content,
                "original_content": content,
                "validation_applied": False,
                "reason": "XPIA middleware disabled",
            }

        start_time = time.time()

        try:
            # Extract context information
            user_context = self._extract_user_context(context)

            # Perform validation with strict mode for user input
            result = self.defense_agent.validate_user_input(
                content, user_context=user_context
            )

            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            self._update_stats(result, processing_time)

            # Log security decision
            self._log_security_decision(result, "user_input", user_context)

            # Determine action based on result
            return self._process_validation_result(result, "user_input")

        except Exception as e:
            self.logger.error(f"XPIA validation failed: {e}")

            # Fail-safe: block content on validation error in strict mode
            if self.config["block_on_critical"]:
                return {
                    "safe": False,
                    "content": "[BLOCKED: Validation error]",
                    "original_content": content,
                    "validation_applied": True,
                    "error": str(e),
                    "reason": "Validation system error - fail-safe activated",
                }
            else:
                return {
                    "safe": True,
                    "content": content,
                    "original_content": content,
                    "validation_applied": False,
                    "error": str(e),
                    "reason": "Validation error - content allowed due to permissive config",
                }

    def validate_agent_communication(
        self, content: str, source_agent: str = "unknown", target_agent: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Validate inter-agent communication.

        Args:
            content: Communication content to validate
            source_agent: Name of source agent
            target_agent: Name of target agent

        Returns:
            Dictionary with validation results and processed content
        """
        if not self.config["enabled"]:
            return {
                "safe": True,
                "content": content,
                "original_content": content,
                "validation_applied": False,
                "reason": "XPIA middleware disabled",
            }

        start_time = time.time()

        try:
            # Perform validation
            result = self.defense_agent.validate_agent_communication(
                content, source_agent=source_agent, target_agent=target_agent
            )

            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            self._update_stats(result, processing_time)

            # Log security decision
            self._log_security_decision(
                result, "agent_communication", f"{source_agent}->{target_agent}"
            )

            # Process result with less strict handling for agent communication
            return self._process_validation_result(result, "agent_communication")

        except Exception as e:
            self.logger.error(f"Agent communication validation failed: {e}")

            # For agent communication, be less strict on errors
            return {
                "safe": True,
                "content": content,
                "original_content": content,
                "validation_applied": False,
                "error": str(e),
                "reason": "Agent communication validation error - content allowed",
            }

    def validate_file_content(
        self, content: str, filename: str = "unknown", file_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Validate file content before processing.

        Args:
            content: File content to validate
            filename: Name of the file
            file_type: Type/extension of the file

        Returns:
            Dictionary with validation results and processed content
        """
        if not self.config["enabled"]:
            return {
                "safe": True,
                "content": content,
                "original_content": content,
                "validation_applied": False,
                "reason": "XPIA middleware disabled",
            }

        start_time = time.time()

        try:
            # Perform validation
            result = self.defense_agent.validate_file_content(content, filename)

            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            self._update_stats(result, processing_time)

            # Log security decision
            self._log_security_decision(
                result, "file_content", f"{filename} ({file_type})"
            )

            # Process result
            return self._process_validation_result(result, "file_content")

        except Exception as e:
            self.logger.error(f"File content validation failed: {e}")

            # For file content, apply fail-safe based on file type
            if file_type in ["sh", "bash", "py", "js", "executable"]:
                return {
                    "safe": False,
                    "content": "[BLOCKED: Validation error on executable content]",
                    "original_content": content,
                    "validation_applied": True,
                    "error": str(e),
                    "reason": "Executable file validation error - fail-safe activated",
                }
            else:
                return {
                    "safe": True,
                    "content": content,
                    "original_content": content,
                    "validation_applied": False,
                    "error": str(e),
                    "reason": "Non-executable file validation error - content allowed",
                }

    def _extract_user_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Extract user context information"""
        if not context:
            return "general"

        # Build context string from available information
        context_parts = []

        if "source" in context:
            context_parts.append(f"source:{context['source']}")
        if "operation" in context:
            context_parts.append(f"op:{context['operation']}")
        if "agent" in context:
            context_parts.append(f"agent:{context['agent']}")

        return "_".join(context_parts) if context_parts else "general"

    def _process_validation_result(
        self, result: ValidationResult, context_type: str
    ) -> Dict[str, Any]:
        """Process validation result and determine action"""
        # Determine if content should be blocked
        should_block = False

        if result.threat_level.value == "critical":
            should_block = self.config["block_on_critical"]
        elif result.threat_level.value == "malicious":
            should_block = True  # Always block malicious content
        elif result.threat_level.value == "suspicious":
            should_block = (
                context_type == "user_input" and self.config["strict_user_input"]
            )

        # Create response
        response = {
            "safe": result.is_safe and not should_block,
            "content": result.sanitized_content if not should_block else "[BLOCKED]",
            "original_content": result.original_content,
            "validation_applied": True,
            "threat_level": result.threat_level.value,
            "threats_detected": len(result.threats_detected),
            "processing_time_ms": result.processing_time_ms,
            "content_hash": result.content_hash,
        }

        # Add detailed information if threats were detected
        if result.threats_detected:
            response["threat_details"] = [
                {
                    "pattern": threat["pattern_name"],
                    "category": threat["category"],
                    "description": threat["description"],
                    "confidence": threat.get("confidence", 1.0),
                }
                for threat in result.threats_detected
            ]

            response["sanitization_applied"] = result.sanitization_applied

        # Add reason for decision
        if should_block:
            response["reason"] = (
                f"Blocked due to {result.threat_level.value} threat level"
            )
        elif result.threats_detected:
            response["reason"] = (
                f"Allowed with sanitization - {len(result.threats_detected)} threats mitigated"
            )
        else:
            response["reason"] = "No threats detected - content allowed"

        return response

    def _update_stats(self, result: ValidationResult, processing_time: float):
        """Update middleware statistics"""
        self.stats["total_validations"] += 1
        self.stats["total_processing_time_ms"] += processing_time
        self.stats["average_latency_ms"] = (
            self.stats["total_processing_time_ms"] / self.stats["total_validations"]
        )

        if not result.is_safe:
            if result.threat_level.value in ["critical", "malicious"]:
                self.stats["threats_blocked"] += 1
            else:
                self.stats["threats_warned"] += 1

    def _log_security_decision(
        self, result: ValidationResult, context_type: str, context_detail: str
    ):
        """Log security decision for audit trail"""
        security_logger = logging.getLogger("xpia_middleware_security")

        log_level = logging.INFO
        if result.threat_level.value == "critical":
            log_level = logging.CRITICAL
        elif result.threat_level.value == "malicious":
            log_level = logging.ERROR
        elif result.threat_level.value == "suspicious":
            log_level = logging.WARNING

        security_logger.log(
            log_level,
            f"XPIA Middleware Decision - Context: {context_type}:{context_detail}, "
            f"Safe: {result.is_safe}, Threat Level: {result.threat_level.value}, "
            f"Threats: {len(result.threats_detected)}, "
            f"Processing: {result.processing_time_ms:.2f}ms, Hash: {result.content_hash}",
        )

        # Log individual threats if present
        if result.threats_detected and (
            self.config["log_all_validations"] or not result.is_safe
        ):
            for threat in result.threats_detected:
                security_logger.log(
                    log_level,
                    f"Threat Detail - Pattern: {threat['pattern_name']}, "
                    f"Category: {threat['category']}, "
                    f"Match: '{threat['match_text'][:50]}...'",
                )

    def get_middleware_status(self) -> Dict[str, Any]:
        """Get comprehensive middleware status"""
        defense_status = self.defense_agent.get_security_status()

        return {
            "middleware_status": "enabled" if self.config["enabled"] else "disabled",
            "security_mode": defense_status["security_mode"],
            "configuration": self.config.copy(),
            "statistics": self.stats.copy(),
            "defense_engine_status": defense_status,
            "performance_summary": {
                "total_validations": self.stats["total_validations"],
                "average_latency_ms": self.stats["average_latency_ms"],
                "threats_blocked": self.stats["threats_blocked"],
                "threats_warned": self.stats["threats_warned"],
                "block_rate": (
                    self.stats["threats_blocked"]
                    / max(self.stats["total_validations"], 1)
                    * 100
                ),
            },
        }

    def update_configuration(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update middleware configuration"""
        old_config = self.config.copy()

        # Update configuration
        for key, value in new_config.items():
            if key in self.config:
                self.config[key] = value

        # Log configuration change
        self.logger.info(f"XPIA Middleware configuration updated: {new_config}")

        # If security mode changed, update defense agent
        if "security_mode" in new_config:
            try:
                new_mode = SecurityMode(new_config["security_mode"])
                self.defense_agent.engine.update_security_mode(new_mode)
            except ValueError:
                self.logger.error(
                    f"Invalid security mode: {new_config['security_mode']}"
                )

        return {
            "success": True,
            "old_config": old_config,
            "new_config": self.config.copy(),
        }

# Global middleware instance for hook integration
_xpia_middleware_instance = None

def get_xpia_middleware(
    security_mode: SecurityMode = SecurityMode.BALANCED,
) -> XPIAMiddleware:
    """Get or create the global XPIA middleware instance"""
    global _xpia_middleware_instance

    if _xpia_middleware_instance is None:
        _xpia_middleware_instance = XPIAMiddleware(security_mode)

    return _xpia_middleware_instance

def xpia_validate_user_input(
    content: str, context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Hook function for validating user input"""
    middleware = get_xpia_middleware()
    return middleware.validate_user_input(content, context)

def xpia_validate_agent_communication(
    content: str, source_agent: str = "unknown", target_agent: str = "unknown"
) -> Dict[str, Any]:
    """Hook function for validating agent communication"""
    middleware = get_xpia_middleware()
    return middleware.validate_agent_communication(content, source_agent, target_agent)

def xpia_validate_file_content(
    content: str, filename: str = "unknown", file_type: str = "unknown"
) -> Dict[str, Any]:
    """Hook function for validating file content"""
    middleware = get_xpia_middleware()
    return middleware.validate_file_content(content, filename, file_type)

def xpia_get_status() -> Dict[str, Any]:
    """Hook function for getting XPIA middleware status"""
    middleware = get_xpia_middleware()
    return middleware.get_middleware_status()

def xpia_update_config(new_config: Dict[str, Any]) -> Dict[str, Any]:
    """Hook function for updating XPIA configuration"""
    middleware = get_xpia_middleware()
    return middleware.update_configuration(new_config)
