"""Type stubs for error_handling module."""

from typing import Any, Callable, Dict, List, Optional, Type
from enum import Enum
import logging

logger: logging.Logger

class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW: str
    MEDIUM: str
    HIGH: str
    CRITICAL: str

class RetryStrategy(Enum):
    """Retry strategies."""

    EXPONENTIAL: str
    LINEAR: str
    FIXED: str

class GadugiError(Exception):
    """Base error for Gadugi operations."""

    severity: ErrorSeverity
    context: Dict[str, Any]
    def __init__(
        self, message: str, severity: ErrorSeverity = ..., context: Optional[Dict[str, Any]] = None
    ) -> None: ...

class RecoverableError(GadugiError):
    """Error that can potentially be recovered from."""

    ...

class NonRecoverableError(GadugiError):
    """Error that cannot be recovered from."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None: ...

class ErrorContext:
    """Context manager for error handling."""
    def __init__(
        self,
        operation_name: str,
        severity: ErrorSeverity = ...,
        fallback: Optional[Callable] = None,
    ) -> None: ...
    def __enter__(self) -> "ErrorContext": ...
    def __exit__(
        self, exc_type: Optional[Type[Exception]], exc_val: Optional[Exception], exc_tb: Any
    ) -> bool: ...

class ErrorHandler:
    """Central error handler for the system."""
    def __init__(self) -> None: ...
    def handle(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None: ...
    def handle_async(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None: ...
    def get_recovery_strategy(self, error: Exception) -> Optional[Callable]: ...
    def register_recovery_strategy(
        self, error_type: Type[Exception], strategy: Callable
    ) -> None: ...
    def aggregate_errors(self, errors: List[Exception]) -> Optional[Exception]: ...

class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    failure_threshold: int
    recovery_timeout: float
    failure_count: int
    last_failure_time: Optional[float]
    is_open: bool
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0) -> None: ...
    def __call__(self, func: Callable) -> Callable: ...
    def reset(self) -> None: ...
    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any: ...

def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    strategy: RetryStrategy = ...,
    backoff_factor: float = 2.0,
    exceptions: tuple = ...,
    on_retry: Optional[Callable] = None,
) -> Callable: ...
def graceful_degradation(fallback: Callable) -> Callable: ...
def handle_with_fallback(primary: Callable, fallback: Callable) -> Any: ...
def validate_input(schema: Dict[str, Any]) -> Callable: ...
