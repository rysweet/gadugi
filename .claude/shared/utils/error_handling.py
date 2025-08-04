"""
Error handling utilities for Gadugi multi-agent system.
Provides retry logic, graceful degradation, and error recovery patterns.
"""

import time
import functools
import logging
from typing import Callable, Any, Optional, Dict, List, Type
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(Enum):
    """Retry strategies."""

    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class GadugiError(Exception):
    """Base exception for Gadugi system."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.severity = severity
        self.context = context or {}


class RecoverableError(GadugiError):
    """Error that can potentially be recovered from."""

    pass


class NonRecoverableError(GadugiError):
    """Error that cannot be recovered from."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorSeverity.CRITICAL, context)


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
    Decorator for retry logic with various strategies.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        strategy: Retry strategy to use
        backoff_factor: Factor for exponential/linear backoff
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            delay = initial_delay
            last_exception = None

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    last_exception = e

                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}"
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(delay)

                    # Calculate next delay
                    if strategy == RetryStrategy.EXPONENTIAL:
                        delay *= backoff_factor
                    elif strategy == RetryStrategy.LINEAR:
                        delay += initial_delay * (backoff_factor - 1)
                    # FIXED strategy keeps the same delay

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def graceful_degradation(
    fallback_value: Any = None,
    log_errors: bool = True,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for graceful degradation on errors.

    Args:
        fallback_value: Value to return on error
        log_errors: Whether to log errors
        exceptions: Tuple of exceptions to handle
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    logger.error(f"{func.__name__} failed, using fallback: {e}")
                return fallback_value

        return wrapper

    return decorator


class ErrorHandler:
    """Centralized error handling with recovery strategies."""

    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
        self.error_history: List[Dict[str, Any]] = []

    def register_recovery_strategy(
        self, exception_type: Type[Exception], strategy: Callable
    ):
        """Register a recovery strategy for specific exception type."""
        self.recovery_strategies[exception_type] = strategy

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        Handle error with appropriate recovery strategy.

        Args:
            error: The exception that occurred
            context: Context information about the error

        Returns:
            Recovery result or re-raises if no recovery possible
        """
        error_key = f"{type(error).__name__}:{str(error)}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Record error history
        self.error_history.append(
            {
                "timestamp": time.time(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "count": self.error_counts[error_key],
            }
        )

        # Find recovery strategy
        for exc_type, strategy in self.recovery_strategies.items():
            if isinstance(error, exc_type):
                logger.info(f"Applying recovery strategy for {exc_type.__name__}")
                return strategy(error, context)

        # No recovery strategy found
        logger.error(f"No recovery strategy for {type(error).__name__}: {error}")
        raise error

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "unique_errors": len(self.error_counts),
            "top_errors": sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "recent_errors": self.error_history[-10:],
        }

    def reset_statistics(self):
        """Reset error statistics."""
        self.error_counts.clear()
        self.error_history.clear()


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents repeated calls to failing services.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check if circuit should be reset
            if self.is_open and self.last_failure_time:
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    logger.info(f"Circuit breaker reset for {func.__name__}")
                    self.reset()

            # If circuit is open, fail fast
            if self.is_open:
                raise NonRecoverableError(
                    f"Circuit breaker open for {func.__name__}",
                    {"failure_count": self.failure_count},
                )

            try:
                result = func(*args, **kwargs)
                # Success - reset failure count
                if self.failure_count > 0:
                    logger.info(
                        f"Success after {self.failure_count} failures for {func.__name__}"
                    )
                self.failure_count = 0
                return result

            except Exception:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.is_open = True
                    logger.error(
                        f"Circuit breaker opened for {func.__name__} "
                        f"after {self.failure_count} failures"
                    )

                raise

        return wrapper

    def reset(self):
        """Reset circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call a function with circuit breaker protection."""
        # Check if circuit should be reset
        if self.is_open and self.last_failure_time:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit breaker reset for function call")
                self.reset()

        # If circuit is open, fail fast
        if self.is_open:
            raise NonRecoverableError(
                f"Circuit breaker open for function call",
                {'failure_count': self.failure_count}
            )

        try:
            result = func(*args, **kwargs)
            # Reset failure count on success
            if self.failure_count > 0:
                logger.info(f"Circuit breaker reset after successful call")
                self.failure_count = 0
                self.last_failure_time = None
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

            raise


def handle_with_fallback(
    primary_func: Callable, fallback_func: Callable, exceptions: tuple = (Exception,)
) -> Any:
    """
    Execute primary function with fallback on failure.

    Args:
        primary_func: Primary function to execute
        fallback_func: Fallback function if primary fails
        exceptions: Exceptions to catch

    Returns:
        Result from primary or fallback function
    """
    try:
        return primary_func()
    except exceptions as e:
        logger.warning(f"Primary function failed, using fallback: {e}")
        return fallback_func()


class ErrorContext:
    """Context manager for error handling with cleanup."""

    def __init__(
        self,
        operation_name: str,
        cleanup_func: Optional[Callable] = None,
        suppress_errors: bool = False,
    ):
        self.operation_name = operation_name
        self.cleanup_func = cleanup_func
        self.suppress_errors = suppress_errors
        self.error = None

    def __enter__(self):
        logger.debug(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.error = exc_val
            logger.error(f"Error in {self.operation_name}: {exc_val}")

            if self.cleanup_func:
                try:
                    logger.info(f"Running cleanup for {self.operation_name}")
                    self.cleanup_func()
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {cleanup_error}")

        logger.debug(f"Completed operation: {self.operation_name}")

        # Suppress errors if requested
        return self.suppress_errors


def validate_input(validation_rules: Dict[str, Callable]) -> Callable:
    """
    Decorator for input validation.

    Args:
        validation_rules: Dictionary mapping parameter names to validation functions
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get function signature
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each parameter
            for param_name, validator in validation_rules.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for {param_name}: {value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator
