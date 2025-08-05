from datetime import timedelta
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
import uuid
import sys
import os
from error_handling import GadugiError

"""
Audit Logger for Container Execution.

Provides comprehensive audit logging for container execution activities,
including security events, resource usage, and operational activities.
"""


# Import Enhanced Separation shared modules

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", ".claude", "shared", "utils")
)
logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""

    CONTAINER_CREATED = "container_created"
    CONTAINER_STARTED = "container_started"
    CONTAINER_STOPPED = "container_stopped"
    CONTAINER_FAILED = "container_failed"
    CONTAINER_REMOVED = "container_removed"
    SECURITY_VIOLATION = "security_violation"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    POLICY_APPLIED = "policy_applied"
    EXECUTION_COMPLETED = "execution_completed"
    ACCESS_DENIED = "access_denied"
    AUTHENTICATION_FAILED = "authentication_failed"
    CONFIGURATION_CHANGED = "configuration_changed"
    SYSTEM_ERROR = "system_error"


class AuditSeverity(Enum):
    """Audit event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event structure."""

    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    container_id: Optional[str]
    user_id: Optional[str]
    source_ip: Optional[str]
    message: str
    details: Dict[str, Any]
    resource_usage: Optional[Dict[str, Any]] = None
    security_context: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None


class AuditLogger:
    """
    Comprehensive audit logging for container execution environment.

    Provides tamper-evident logging, structured event recording,
    and audit trail maintenance for security and compliance.
    """

    def __init__(
        self,
        log_directory: Optional[Path] = None,
        max_log_size: int = 100 * 1024 * 1024,  # 100MB
        retention_days: int = 90,
    ):
        """
        Initialize audit logger.

        Args:
            log_directory: Directory for audit logs
            max_log_size: Maximum size per log file
            retention_days: Number of days to retain logs
        """
        self.log_directory = log_directory or Path("logs/audit")
        self.log_directory.mkdir(parents=True, exist_ok=True)

        self.max_log_size = max_log_size
        self.retention_days = retention_days
        self.current_log_file: Optional[Path] = None
        self.current_log_size = 0

        # Security features
        self.log_integrity_enabled = True
        self.previous_event_hash = ""

        # Initialize current log file
        self._initialize_log_file()

        logger.info(f"Audit logger initialized with directory: {self.log_directory}")

    def _initialize_log_file(self) -> None:
        """Initialize current log file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = self.log_directory / f"audit_{timestamp}.jsonl"
        self.current_log_size = 0

        # Write log file header
        header = {
            "log_initialized": datetime.now().isoformat(),
            "version": "1.0",
            "integrity_enabled": self.log_integrity_enabled,
        }

        self._write_raw_entry(header)
        logger.info(f"Initialized audit log file: {self.current_log_file}")

    def _rotate_log_file(self) -> None:
        """Rotate to new log file when current file is too large."""
        if self.current_log_size >= self.max_log_size:
            logger.info(
                f"Rotating audit log file (size: {self.current_log_size} bytes)"
            )
            self._initialize_log_file()

    def _calculate_event_checksum(self, event: AuditEvent) -> str:
        """Calculate tamper-evident checksum for audit event."""
        if not self.log_integrity_enabled:
            return ""

        # Create deterministic string representation
        event_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "container_id": event.container_id,
            "message": event.message,
            "details": event.details,
            "previous_hash": self.previous_event_hash,
        }

        event_json = json.dumps(event_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(event_json.encode("utf-8")).hexdigest()

    def _write_raw_entry(self, data: Dict[str, Any]) -> None:
        """Write raw data entry to log file."""
        try:
            with open(self.current_log_file, "a", encoding="utf-8") as f:
                json_line = json.dumps(data, default=str) + "\n"
                f.write(json_line)
                f.flush()  # Ensure immediate write

                self.current_log_size += len(json_line.encode("utf-8"))

        except Exception as e:
            logger.error(f"Failed to write audit log entry: {e}")
            raise GadugiError(f"Audit logging failed: {e}")

    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        message: str,
        container_id: Optional[str] = None,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        resource_usage: Optional[Dict[str, Any]] = None,
        security_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an audit event.

        Args:
            event_type: Type of audit event
            severity: Event severity level
            message: Human-readable message
            container_id: Related container ID
            user_id: User associated with event
            source_ip: Source IP address
            details: Additional event details
            resource_usage: Resource usage information
            security_context: Security context information

        Returns:
            Event ID for reference
        """
        event_id = str(uuid.uuid4())

        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            container_id=container_id,
            user_id=user_id,
            source_ip=source_ip,
            message=message,
            details=details or {},
            resource_usage=resource_usage,
            security_context=security_context,
        )

        # Calculate integrity checksum
        event.checksum = self._calculate_event_checksum(event)

        # Convert to dictionary for logging
        event_dict = asdict(event)

        # Convert enum values to strings
        event_dict["event_type"] = event.event_type.value
        event_dict["severity"] = event.severity.value
        event_dict["timestamp"] = event.timestamp.isoformat()

        # Write to log file
        self._write_raw_entry(event_dict)

        # Update hash chain for next event
        if self.log_integrity_enabled:
            self.previous_event_hash = event.checksum

        # Rotate log file if needed
        self._rotate_log_file()

        # Log to standard logger for real-time monitoring
        log_level = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }.get(severity, logging.INFO)

        logger.log(log_level, f"AUDIT [{event_type.value}] {message}")

        return event_id

    def log_container_created(
        self,
        container_id: str,
        image: str,
        command: List[str],
        security_policy: str,
        resource_limits: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> str:
        """Log container creation event."""
        return self.log_event(
            event_type=AuditEventType.CONTAINER_CREATED,
            severity=AuditSeverity.INFO,
            message=f"Container created: {container_id[:8]}",
            container_id=container_id,
            user_id=user_id,
            details={
                "image": image,
                "command": command,
                "security_policy": security_policy,
                "resource_limits": resource_limits,
            },
        )

    def log_container_started(
        self, container_id: str, user_id: Optional[str] = None
    ) -> str:
        """Log container start event."""
        return self.log_event(
            event_type=AuditEventType.CONTAINER_STARTED,
            severity=AuditSeverity.INFO,
            message=f"Container started: {container_id[:8]}",
            container_id=container_id,
            user_id=user_id,
        )

    def log_container_stopped(
        self,
        container_id: str,
        exit_code: int,
        execution_time: float,
        resource_usage: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> str:
        """Log container stop event."""
        severity = AuditSeverity.INFO if exit_code == 0 else AuditSeverity.WARNING

        return self.log_event(
            event_type=AuditEventType.CONTAINER_STOPPED,
            severity=severity,
            message=f"Container stopped: {container_id[:8]} (exit_code={exit_code})",
            container_id=container_id,
            user_id=user_id,
            details={"exit_code": exit_code, "execution_time_seconds": execution_time},
            resource_usage=resource_usage,
        )

    def log_container_failed(
        self, container_id: str, error: str, user_id: Optional[str] = None
    ) -> str:
        """Log container failure event."""
        return self.log_event(
            event_type=AuditEventType.CONTAINER_FAILED,
            severity=AuditSeverity.ERROR,
            message=f"Container failed: {container_id[:8]}",
            container_id=container_id,
            user_id=user_id,
            details={"error": error},
        )

    def log_security_violation(
        self,
        container_id: str,
        violation_type: str,
        description: str,
        security_context: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> str:
        """Log security violation event."""
        return self.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=AuditSeverity.CRITICAL,
            message=f"Security violation in {container_id[:8]}: {violation_type}",
            container_id=container_id,
            user_id=user_id,
            details={"violation_type": violation_type, "description": description},
            security_context=security_context,
        )

    def log_resource_limit_exceeded(
        self,
        container_id: str,
        resource_type: str,
        limit: float,
        actual: float,
        user_id: Optional[str] = None,
    ) -> str:
        """Log resource limit exceeded event."""
        return self.log_event(
            event_type=AuditEventType.RESOURCE_LIMIT_EXCEEDED,
            severity=AuditSeverity.WARNING,
            message=f"Resource limit exceeded in {container_id[:8]}: {resource_type}",
            container_id=container_id,
            user_id=user_id,
            details={
                "resource_type": resource_type,
                "limit": limit,
                "actual": actual,
                "percentage": (actual / limit * 100) if limit > 0 else 0,
            },
        )

    def log_policy_applied(
        self,
        container_id: str,
        policy_name: str,
        policy_details: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> str:
        """Log security policy application event."""
        return self.log_event(
            event_type=AuditEventType.POLICY_APPLIED,
            severity=AuditSeverity.INFO,
            message=f"Security policy '{policy_name}' applied to {container_id[:8]}",
            container_id=container_id,
            user_id=user_id,
            details=policy_details,
            security_context={"policy": policy_name},
        )

    def log_access_denied(
        self,
        container_id: str,
        requested_action: str,
        reason: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Log access denied event."""
        return self.log_event(
            event_type=AuditEventType.ACCESS_DENIED,
            severity=AuditSeverity.WARNING,
            message=f"Access denied for {container_id[:8]}: {requested_action}",
            container_id=container_id,
            user_id=user_id,
            details={"requested_action": requested_action, "denial_reason": reason},
        )

    def search_events(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        container_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Search audit events with filters.

        Args:
            event_type: Filter by event type
            severity: Filter by severity
            container_id: Filter by container ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return

        Returns:
            List of matching audit events
        """
        events = []

        try:
            # Search through all log files
            log_files = sorted(self.log_directory.glob("audit_*.jsonl"))

            for log_file in log_files:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())

                            # Skip header entries
                            if "log_initialized" in event:
                                continue

                            # Apply filters
                            if (
                                event_type
                                and event.get("event_type") != event_type.value
                            ):
                                continue

                            if severity and event.get("severity") != severity.value:
                                continue

                            if (
                                container_id
                                and event.get("container_id") != container_id
                            ):
                                continue

                            # Time filters
                            event_time = datetime.fromisoformat(
                                event.get("timestamp", "")
                            )

                            if start_time and event_time < start_time:
                                continue

                            if end_time and event_time > end_time:
                                continue

                            events.append(event)

                            # Respect limit
                            if len(events) >= limit:
                                break

                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"Invalid audit log entry: {e}")
                            continue

                # Break if we've reached the limit
                if len(events) >= limit:
                    break

        except Exception as e:
            logger.error(f"Error searching audit events: {e}")
            raise GadugiError(f"Audit search failed: {e}")

        return events[-limit:]  # Return most recent events

    def get_statistics(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit statistics for a time period."""
        events = self.search_events(start_time=start_time, end_time=end_time)

        stats = {
            "total_events": len(events),
            "events_by_type": {},
            "events_by_severity": {},
            "containers_affected": set(),
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
        }

        for event in events:
            # Count by type
            event_type = event.get("event_type", "unknown")
            stats["events_by_type"][event_type] = (
                stats["events_by_type"].get(event_type, 0) + 1
            )

            # Count by severity
            severity = event.get("severity", "unknown")
            stats["events_by_severity"][severity] = (
                stats["events_by_severity"].get(severity, 0) + 1
            )

            # Track affected containers
            if event.get("container_id"):
                stats["containers_affected"].add(event["container_id"])

        stats["unique_containers"] = len(stats["containers_affected"])
        stats["containers_affected"] = list(stats["containers_affected"])

        return stats

    def verify_log_integrity(self, log_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Verify integrity of audit log using checksums.

        Args:
            log_file: Specific log file to verify, or current file if None

        Returns:
            Verification results
        """
        if not self.log_integrity_enabled:
            return {"integrity_enabled": False, "status": "skipped"}

        file_to_verify = log_file or self.current_log_file

        try:
            events_verified = 0
            events_failed = 0
            previous_hash = ""

            with open(file_to_verify, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        event = json.loads(line.strip())

                        # Skip header entries
                        if "log_initialized" in event:
                            continue

                        # Verify checksum if present
                        if "checksum" in event:
                            # Recreate the event for verification
                            temp_event = AuditEvent(
                                event_id=event["event_id"],
                                timestamp=datetime.fromisoformat(event["timestamp"]),
                                event_type=AuditEventType(event["event_type"]),
                                severity=AuditSeverity(event["severity"]),
                                container_id=event.get("container_id"),
                                user_id=event.get("user_id"),
                                source_ip=event.get("source_ip"),
                                message=event["message"],
                                details=event.get("details", {}),
                                resource_usage=event.get("resource_usage"),
                                security_context=event.get("security_context"),
                            )

                            # Calculate expected checksum
                            old_previous_hash = self.previous_event_hash
                            self.previous_event_hash = previous_hash
                            expected_checksum = self._calculate_event_checksum(
                                temp_event
                            )
                            self.previous_event_hash = old_previous_hash

                            if expected_checksum == event["checksum"]:
                                events_verified += 1
                            else:
                                events_failed += 1
                                logger.warning(
                                    f"Integrity violation at line {line_num}"
                                )

                            previous_hash = event["checksum"]

                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        logger.warning(f"Invalid entry at line {line_num}: {e}")
                        events_failed += 1

            return {
                "integrity_enabled": True,
                "status": "verified" if events_failed == 0 else "failed",
                "events_verified": events_verified,
                "events_failed": events_failed,
                "file_verified": str(file_to_verify),
            }

        except Exception as e:
            logger.error(f"Error verifying log integrity: {e}")
            return {"integrity_enabled": True, "status": "error", "error": str(e)}

    def cleanup_old_logs(self) -> int:
        """Clean up old audit logs based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        files_removed = 0

        try:
            for log_file in self.log_directory.glob("audit_*.jsonl"):
                # Check if file is older than retention period
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    files_removed += 1
                    logger.info(f"Removed old audit log: {log_file}")

        except Exception as e:
            logger.error(f"Error during log cleanup: {e}")

        return files_removed
