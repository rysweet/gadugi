"""Type stubs for error_handling module."""

from typing import Any, Callable, Dict, List, Optional, Type, Tuple
from enum import Enum

class ErrorSeverity(Enum):
    LOW: str
    MEDIUM: str
    HIGH: str
    CRITICAL: str

class ErrorCategory(Enum):
    WORKFLOW_EXECUTION: str
    SYSTEM: str
    VALIDATION: str
    NETWORK: str
    AUTHENTICATION: str
    CONFIGURATION: str

class RetryStrategy(Enum):
    EXPONENTIAL: str
    LINEAR: str
    FIXED: str

class GadugiError(Exception):
    severity: ErrorSeverity
    context: Dict[str, Any]
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ...,
        context: Optional[Dict[str, Any]] = None,
    ) -> None: ...

class RecoverableError(GadugiError): ...

class NonRecoverableError(GadugiError):
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None: ...

class ErrorHandler:
    error_counts: Dict[str, int]
    recovery_strategies: Dict[Type[Exception], Callable]
    error_history: List[Dict[str, Any]]
    
    def __init__(self) -> None: ...
    def register_recovery_strategy(
        self, exception_type: Type[Exception], strategy: Callable
    ) -> None: ...
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Any: ...
    def get_error_statistics(self) -> Dict[str, Any]: ...
    def reset_statistics(self) -> None: ...

class CircuitBreaker:
    failure_threshold: int
    recovery_timeout: float
    failure_count: int
    last_failure_time: Optional[float]
    is_open: bool
    
    def __init__(self, failure_threshold: int, recovery_timeout: float) -> None: ...
    def __call__(self, func: Callable) -> Callable: ...
    def reset(self) -> None: ...
    def call(self, func: Callable, *args, **kwargs) -> Any: ...

class ErrorContext:
    operation_name: str
    cleanup_func: Optional[Callable]
    suppress_errors: bool
    error: Optional[Exception]
    
    def __init__(
        self,
        operation_name: str,
        cleanup_func: Optional[Callable] = None,
        suppress_errors: bool = False,
    ) -> None: ...
    def __enter__(self) -> 'ErrorContext': ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool: ...

def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    strategy: RetryStrategy = ...,
    backoff_factor: float = 2.0,
    exceptions: Tuple = ...,
    on_retry: Optional[Callable] = None,
) -> Callable: ...

def graceful_degradation(
    fallback_value: Any = None,
    log_errors: bool = True,
    exceptions: Tuple = ...,
) -> Callable: ...

def handle_with_fallback(
    primary_func: Callable, fallback_func: Callable, exceptions: Tuple = ...
) -> Any: ...

def validate_input(validation_rules: Dict[str, Callable]) -> Callable: ...
