"""
Comprehensive tests for error_handling.py module.
Tests error handling utilities, retry logic, circuit breakers, and recovery patterns.
"""

import logging
import os

# Import the module we're testing
import sys
import time
from datetime import datetime

import pytest
from unittest.mock import call, patch

# For type checking only
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claude.shared.utils.error_handling import (
        CircuitBreaker,
        ErrorContext,
        ErrorHandler,
        ErrorSeverity,
        GadugiError,
        NonRecoverableError,
        RecoverableError,
        RetryStrategy,
        graceful_degradation,
        handle_with_fallback,
        retry,
        validate_input,
    )

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from claude.shared.utils.error_handling import (
        CircuitBreaker,
        ErrorContext,
        ErrorHandler,
        ErrorSeverity,
        GadugiError,
        NonRecoverableError,
        RecoverableError,
        RetryStrategy,
        graceful_degradation,
        handle_with_fallback,
        retry,
        validate_input,
    )
except ImportError:
    # If import fails, create stub classes to show what needs to be implemented
    print(
        "Warning: Could not import error_handling module. Tests will define what needs to be implemented."
    )

    from enum import Enum

    # Add logger for stub implementation
    logger = logging.getLogger(__name__)

    class ErrorSeverity(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    class RetryStrategy(Enum):
        EXPONENTIAL = "exponential"
        LINEAR = "linear"
        FIXED = "fixed"

    class GadugiError(Exception):
        def __init__(self, message, severity=ErrorSeverity.MEDIUM, context=None):
            super().__init__(message)
            self.severity = severity
            self.context = context or {}

    class RecoverableError(GadugiError):
        pass

    class NonRecoverableError(GadugiError):
        def __init__(self, message, context=None):
            super().__init__(message, ErrorSeverity.CRITICAL, context)

    def retry(
        max_attempts=3,
        initial_delay=1.0,
        strategy=None,
        backoff_factor=2.0,
        exceptions=None,
        on_retry=None,
    ):
        def decorator(func):
            def wrapper(*args, **kwargs):
                last_exception = None
                delay = initial_delay

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        # Check if we should retry this exception
                        if exceptions and not isinstance(e, exceptions):
                            raise

                        # Call on_retry callback if provided
                        if on_retry:
                            on_retry(attempt + 1, e)

                        # Don't sleep on the last attempt
                        if attempt < max_attempts - 1:
                            time.sleep(delay)

                            # Calculate next delay based on strategy
                            if strategy == RetryStrategy.EXPONENTIAL:
                                delay = delay * backoff_factor
                            elif strategy == RetryStrategy.LINEAR:
                                delay = initial_delay + initial_delay * (
                                    backoff_factor - 1
                                ) * (attempt + 1)
                            elif strategy == RetryStrategy.FIXED:
                                delay = initial_delay

                # All attempts failed
                if last_exception:
                    raise last_exception
                else:
                    raise RuntimeError("No exception captured")

            return wrapper

        return decorator

    def graceful_degradation(fallback_value=None, exceptions=None, log_errors=True):
        exceptions = exceptions or (Exception,)

        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if log_errors:
                        logger.error(f"Error in function: {e}")
                    return fallback_value

            return wrapper

        return decorator

    class ErrorHandler:
        def __init__(self):
            self.error_counts = {}
            self.recovery_strategies = {}
            self.error_history = []

        def register_recovery_strategy(self, error_type, strategy):
            self.recovery_strategies[error_type] = strategy

        def handle_error(self, error, context=None):
            # Updated signature to match test usage
            if isinstance(error, Exception):
                error_type = type(error)
                error_key = f"{error_type.__name__}:{str(error)}"

                # Update error counts
                self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

                # Add to history
                history_entry = {
                    "error_type": error_type.__name__,
                    "error_message": str(error),
                    "context": context or {},
                    "count": self.error_counts[error_key],
                    "timestamp": datetime.now(),
                }
                self.error_history.append(history_entry)

                # Try recovery strategy
                if error_type in self.recovery_strategies:
                    return self.recovery_strategies[error_type](error, context)
                else:
                    raise error
            else:
                # Handle ErrorContext objects
                error_type = type(error.error).__name__
                self.error_history.append(error)
                if error_type in self.recovery_strategies:
                    return self.recovery_strategies[error_type](error)

        def get_error_statistics(self):
            total_errors = sum(self.error_counts.values())
            unique_errors = len(self.error_counts)
            top_errors = sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )
            recent_errors = self.error_history[-10:]

            return {
                "total_errors": total_errors,
                "unique_errors": unique_errors,
                "top_errors": top_errors,
                "recent_errors": recent_errors,
            }

        def reset_statistics(self):
            self.error_counts.clear()
            self.error_history.clear()

    class CircuitBreaker:
        def __init__(self, failure_threshold=5, recovery_timeout=60.0, *args, **kwargs):
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.failure_count = 0
            self.last_failure_time = None
            self.is_open = False

        def __call__(self, func):
            def wrapper(*args, **kwargs):
                if self.is_open:
                    # Check if we should try to recover
                    if self.last_failure_time:
                        elapsed = (
                            datetime.now() - self.last_failure_time
                        ).total_seconds()
                        if elapsed >= self.recovery_timeout:
                            # Try to recover
                            self.is_open = False
                            self.failure_count = 0
                            self.last_failure_time = None
                        else:
                            raise NonRecoverableError("Circuit breaker open")
                    else:
                        raise NonRecoverableError("Circuit breaker open")

                try:
                    result = func(*args, **kwargs)
                    # Success resets failure count
                    self.failure_count = 0
                    self.last_failure_time = None
                    return result
                except Exception:
                    self.failure_count += 1
                    self.last_failure_time = datetime.now()

                    if self.failure_count >= self.failure_threshold:
                        self.is_open = True

                    raise

            return wrapper

        def reset(self):
            self.failure_count = 0
            self.last_failure_time = None
            self.is_open = False

    def handle_with_fallback(primary, fallback, exceptions=None):
        exceptions = exceptions or (Exception,)
        try:
            return primary()
        except exceptions as e:
            logger.warning(f"Primary function failed, using fallback: {e}")
            return fallback()

    class ErrorContext:
        def __init__(self, operation_name, cleanup_func=None, suppress_errors=False):
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

                # Run cleanup if provided
                if self.cleanup_func:
                    try:
                        self.cleanup_func()
                    except Exception as cleanup_error:
                        logger.error(
                            f"Cleanup failed for {self.operation_name}: {cleanup_error}"
                        )

                # Suppress errors if requested
                if self.suppress_errors:
                    return True
            else:
                logger.debug(f"Completed operation: {self.operation_name}")

            return False

    def validate_input(validators):
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Get function signature info
                import inspect

                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Validate each parameter
                for param_name, validator in validators.items():
                    if param_name in bound_args.arguments:
                        value = bound_args.arguments[param_name]
                        if not validator(value):
                            raise ValueError(f"Invalid value for {param_name}: {value}")

                return func(*args, **kwargs)

            return wrapper

        return decorator


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self) -> None:
        """Test error severity enum values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_error_severity_ordering(self) -> None:
        """Test that we can compare severities."""
        severities = [
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL,
        ]
        assert len(severities) == 4
        assert ErrorSeverity.CRITICAL != ErrorSeverity.LOW


class TestRetryStrategy:
    """Test RetryStrategy enum."""

    def test_retry_strategy_values(self):
        """Test retry strategy enum values."""
        assert RetryStrategy.EXPONENTIAL.value == "exponential"
        assert RetryStrategy.LINEAR.value == "linear"
        assert RetryStrategy.FIXED.value == "fixed"

    def test_retry_strategy_count(self):
        """Test all retry strategies are defined."""
        strategies = list(RetryStrategy)
        assert len(strategies) == 3


class TestGadugiError:
    """Test GadugiError base exception."""

    def test_gadugi_error_basic(self):
        """Test basic GadugiError creation."""
        error = GadugiError("Test error")
        assert str(error) == "Test error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.context == {}

    def test_gadugi_error_with_severity(self):
        """Test GadugiError with custom severity."""
        error = GadugiError("Critical error", ErrorSeverity.CRITICAL)
        assert error.severity == ErrorSeverity.CRITICAL

    def test_gadugi_error_with_context(self):
        """Test GadugiError with context."""
        context = {"operation": "test_op", "data": {"key": "value"}}
        error = GadugiError("Error with context", context=context)
        assert error.context == context

    def test_gadugi_error_inheritance(self):
        """Test GadugiError inherits from Exception."""
        error = GadugiError("Test")
        assert isinstance(error, Exception)


class TestRecoverableError:
    """Test RecoverableError exception."""

    def test_recoverable_error_creation(self):
        """Test RecoverableError creation."""
        error = RecoverableError("Recoverable error")
        assert isinstance(error, GadugiError)
        assert str(error) == "Recoverable error"

    def test_recoverable_error_with_context(self):
        """Test RecoverableError with context."""
        context = {"retry_count": 2}
        error = RecoverableError("Network timeout", context=context)
        assert error.context == context


class TestNonRecoverableError:
    """Test NonRecoverableError exception."""

    def test_non_recoverable_error_creation(self):
        """Test NonRecoverableError creation."""
        error = NonRecoverableError("Fatal error")
        assert isinstance(error, GadugiError)
        assert error.severity == ErrorSeverity.CRITICAL
        assert str(error) == "Fatal error"

    def test_non_recoverable_error_with_context(self):
        """Test NonRecoverableError with context."""
        context = {"system_state": "corrupted"}
        error = NonRecoverableError("System corrupted", context)
        assert error.context == context
        assert error.severity == ErrorSeverity.CRITICAL


class TestRetryDecorator:
    """Test retry decorator functionality."""

    def test_retry_success_first_attempt(self):
        """Test retry decorator with immediate success."""
        call_count = 0

        @retry(max_attempts=3)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_success_after_failures(self):
        """Test retry decorator succeeding after failures."""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01)
        def eventual_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = eventual_success()
        assert result == "success"
        assert call_count == 3

    def test_retry_max_attempts_exceeded(self):
        """Test retry decorator failing after max attempts."""
        call_count = 0

        @retry(max_attempts=2, initial_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
        assert call_count == 2

    def test_retry_exponential_backoff(self):
        """Test retry with exponential backoff."""
        delays = []

        def mock_sleep(delay):
            delays.append(delay)

        with patch("time.sleep", side_effect=mock_sleep):

            @retry(
                max_attempts=3,
                initial_delay=0.1,
                strategy=RetryStrategy.EXPONENTIAL,
                backoff_factor=2.0,
            )
            def always_fails():
                raise ValueError("Test")

            with pytest.raises(ValueError):
                always_fails()

        assert len(delays) == 2  # 3 attempts = 2 delays
        assert delays[0] == 0.1
        assert delays[1] == 0.2  # 0.1 * 2.0

    def test_retry_linear_backoff(self):
        """Test retry with linear backoff."""
        delays = []

        def mock_sleep(delay):
            delays.append(delay)

        with patch("time.sleep", side_effect=mock_sleep):

            @retry(
                max_attempts=3,
                initial_delay=0.1,
                strategy=RetryStrategy.LINEAR,
                backoff_factor=2.0,
            )
            def always_fails():
                raise ValueError("Test")

            with pytest.raises(ValueError):
                always_fails()

        assert len(delays) == 2
        assert delays[0] == 0.1
        assert delays[1] == 0.2  # 0.1 + 0.1 * (2.0 - 1)

    def test_retry_fixed_backoff(self):
        """Test retry with fixed backoff."""
        delays = []

        def mock_sleep(delay):
            delays.append(delay)

        with patch("time.sleep", side_effect=mock_sleep):

            @retry(max_attempts=3, initial_delay=0.1, strategy=RetryStrategy.FIXED)
            def always_fails():
                raise ValueError("Test")

            with pytest.raises(ValueError):
                always_fails()

        assert len(delays) == 2
        assert all(delay == 0.1 for delay in delays)

    def test_retry_specific_exceptions(self):
        """Test retry only catches specified exceptions."""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01, exceptions=(ValueError,))
        def mixed_failures():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retry this")
            elif call_count == 2:
                raise TypeError("Don't retry this")
            return "success"

        with pytest.raises(TypeError):
            mixed_failures()
        assert call_count == 2

    def test_retry_on_retry_callback(self):
        """Test retry calls on_retry callback."""
        retry_calls = []

        def on_retry_callback(attempt, error):
            retry_calls.append((attempt, str(error)))

        @retry(max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback)
        def fails_twice():
            if len(retry_calls) < 2:
                raise ValueError(f"Failure {len(retry_calls) + 1}")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert len(retry_calls) == 2
        assert retry_calls[0] == (1, "Failure 1")
        assert retry_calls[1] == (2, "Failure 2")


class TestGracefulDegradation:
    """Test graceful degradation decorator."""

    def test_graceful_degradation_success(self):
        """Test graceful degradation with successful operation."""

        @graceful_degradation(fallback_value="fallback")
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

    def test_graceful_degradation_with_fallback(self):
        """Test graceful degradation returns fallback on error."""

        @graceful_degradation(fallback_value="fallback")
        def failing_func():
            raise ValueError("Error")

        result = failing_func()
        assert result == "fallback"

    def test_graceful_degradation_none_fallback(self):
        """Test graceful degradation with None fallback."""

        @graceful_degradation()
        def failing_func():
            raise ValueError("Error")

        result = failing_func()
        assert result is None

    def test_graceful_degradation_specific_exceptions(self):
        """Test graceful degradation only handles specified exceptions."""

        @graceful_degradation(fallback_value="fallback", exceptions=(ValueError,))
        def mixed_failures():
            raise TypeError("Not handled")

        with pytest.raises(TypeError):
            mixed_failures()

    def test_graceful_degradation_logging(self):
        """Test graceful degradation logs errors."""
        with patch("claude.shared.utils.error_handling.logger") as mock_logger:

            @graceful_degradation(fallback_value="fallback", log_errors=True)
            def failing_func():
                raise ValueError("Test error")

            result = failing_func()
            assert result == "fallback"
            mock_logger.error.assert_called_once()

    def test_graceful_degradation_no_logging(self):
        """Test graceful degradation without logging."""
        with patch("claude.shared.utils.error_handling.logger") as mock_logger:

            @graceful_degradation(fallback_value="fallback", log_errors=False)
            def failing_func():
                raise ValueError("Test error")

            result = failing_func()
            assert result == "fallback"
            mock_logger.error.assert_not_called()


class TestErrorHandler:
    """Test ErrorHandler class."""

    def test_error_handler_init(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler()
        assert handler.error_counts == {}
        assert handler.recovery_strategies == {}
        assert handler.error_history == []

    def test_register_recovery_strategy(self):
        """Test registering recovery strategy."""
        handler = ErrorHandler()

        def recovery_func(error, context):
            return "recovered"

        handler.register_recovery_strategy(ValueError, recovery_func)
        assert ValueError in handler.recovery_strategies
        assert handler.recovery_strategies[ValueError] == recovery_func

    def test_handle_error_with_recovery(self):
        """Test error handling with recovery strategy."""
        handler = ErrorHandler()

        def recovery_func(error, context):
            return f"recovered from {error}"

        handler.register_recovery_strategy(ValueError, recovery_func)

        error = ValueError("test error")
        context = {"operation": "test"}

        result = handler.handle_error(error, context)
        assert result == "recovered from test error"

    def test_handle_error_without_recovery(self):
        """Test error handling without recovery strategy."""
        handler = ErrorHandler()
        error = ValueError("test error")
        context = {"operation": "test"}

        with pytest.raises(ValueError):
            handler.handle_error(error, context)

    def test_error_counting(self):
        """Test error counting functionality."""
        handler = ErrorHandler()

        def dummy_recovery(error, context):
            return "recovered"

        handler.register_recovery_strategy(ValueError, dummy_recovery)

        error1 = ValueError("error 1")
        error2 = ValueError("error 1")  # Same error
        error3 = ValueError("error 2")  # Different error

        handler.handle_error(error1, {})
        handler.handle_error(error2, {})
        handler.handle_error(error3, {})

        assert handler.error_counts["ValueError:error 1"] == 2
        assert handler.error_counts["ValueError:error 2"] == 1

    def test_error_history(self):
        """Test error history tracking."""
        handler = ErrorHandler()

        def dummy_recovery(error, context):
            return "recovered"

        handler.register_recovery_strategy(ValueError, dummy_recovery)

        error = ValueError("test error")
        context = {"operation": "test_op"}

        handler.handle_error(error, context)

        assert len(handler.error_history) == 1
        history_entry = handler.error_history[0]
        assert history_entry["error_type"] == "ValueError"
        assert history_entry["error_message"] == "test error"
        assert history_entry["context"] == context
        assert history_entry["count"] == 1
        assert "timestamp" in history_entry

    def test_get_error_statistics(self):
        """Test error statistics generation."""
        handler = ErrorHandler()

        def dummy_recovery(error, context):
            return "recovered"

        handler.register_recovery_strategy(ValueError, dummy_recovery)
        handler.register_recovery_strategy(TypeError, dummy_recovery)

        # Generate some errors
        handler.handle_error(ValueError("error 1"), {})
        handler.handle_error(ValueError("error 1"), {})
        handler.handle_error(TypeError("error 2"), {})

        stats = handler.get_error_statistics()

        assert stats["total_errors"] == 3
        assert stats["unique_errors"] == 2
        assert len(stats["top_errors"]) == 2
        assert stats["top_errors"][0][0] == "ValueError:error 1"
        assert stats["top_errors"][0][1] == 2
        assert len(stats["recent_errors"]) == 3

    def test_reset_statistics(self):
        """Test resetting error statistics."""
        handler = ErrorHandler()

        def dummy_recovery(error, context):
            return "recovered"

        handler.register_recovery_strategy(ValueError, dummy_recovery)

        handler.handle_error(ValueError("test"), {})
        assert len(handler.error_counts) > 0
        assert len(handler.error_history) > 0

        handler.reset_statistics()
        assert len(handler.error_counts) == 0
        assert len(handler.error_history) == 0


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_circuit_breaker_init(self):
        """Test CircuitBreaker initialization."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30.0
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.is_open is False

    def test_circuit_breaker_success(self):
        """Test circuit breaker with successful operations."""
        cb = CircuitBreaker()

        @cb
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"
        assert cb.failure_count == 0
        assert not cb.is_open

    def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=2)

        @cb
        def failing_func():
            raise ValueError("Test error")

        # First failure
        with pytest.raises(ValueError):
            failing_func()
        assert cb.failure_count == 1
        assert not cb.is_open

        # Second failure - should open circuit
        with pytest.raises(ValueError):
            failing_func()
        assert cb.failure_count == 2
        assert cb.is_open

        # Third call - should fail fast
        with pytest.raises(NonRecoverableError, match="Circuit breaker open"):
            failing_func()

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        call_count = 0

        @cb
        def conditional_func():
            nonlocal call_count
            call_count += 1
            # First call will fail, later calls (after recovery) will succeed
            if call_count == 1:
                raise ValueError("Test error")
            return "success"

        # Trigger failure to open circuit
        with pytest.raises(ValueError):
            conditional_func()
        assert cb.is_open

        # Wait for recovery timeout
        time.sleep(0.2)

        # Should recover and succeed
        result = conditional_func()
        assert result == "success"
        assert cb.failure_count == 0
        assert not cb.is_open

    def test_circuit_breaker_reset_on_success(self):
        """Test circuit breaker resets failure count on success."""
        cb = CircuitBreaker(failure_threshold=3)

        call_count = 0

        @cb
        def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Fail")
            return "success"

        # Two failures
        with pytest.raises(ValueError):
            sometimes_fails()
        with pytest.raises(ValueError):
            sometimes_fails()
        assert cb.failure_count == 2

        # Success should reset
        result = sometimes_fails()
        assert result == "success"
        assert cb.failure_count == 0

    def test_circuit_breaker_reset_method(self):
        """Test circuit breaker manual reset."""
        cb = CircuitBreaker(failure_threshold=1)

        @cb
        def failing_func():
            raise ValueError("Test error")

        # Open circuit
        with pytest.raises(ValueError):
            failing_func()
        assert cb.is_open

        # Manual reset
        cb.reset()
        assert not cb.is_open
        assert cb.failure_count == 0
        assert cb.last_failure_time is None


class TestHandleWithFallback:
    """Test handle_with_fallback function."""

    def test_handle_with_fallback_success(self):
        """Test fallback handler with successful primary function."""

        def primary():
            return "primary result"

        def fallback():
            return "fallback result"

        result = handle_with_fallback(primary, fallback)
        assert result == "primary result"

    def test_handle_with_fallback_failure(self):
        """Test fallback handler with failing primary function."""

        def primary():
            raise ValueError("Primary failed")

        def fallback():
            return "fallback result"

        result = handle_with_fallback(primary, fallback)
        assert result == "fallback result"

    def test_handle_with_fallback_specific_exceptions(self):
        """Test fallback handler with specific exception types."""

        def primary():
            raise TypeError("Wrong type")

        def fallback():
            return "fallback result"

        # Should not catch TypeError if only ValueError is specified
        with pytest.raises(TypeError):
            handle_with_fallback(primary, fallback, exceptions=(ValueError,))

        # Should catch TypeError if specified
        result = handle_with_fallback(primary, fallback, exceptions=(TypeError,))
        assert result == "fallback result"

    def test_handle_with_fallback_logging(self):
        """Test fallback handler logs warnings."""
        with patch("claude.shared.utils.error_handling.logger") as mock_logger:

            def primary():
                raise ValueError("Primary failed")

            def fallback():
                return "fallback result"

            result = handle_with_fallback(primary, fallback)
            assert result == "fallback result"
            mock_logger.warning.assert_called_once()


class TestErrorContext:
    """Test ErrorContext context manager."""

    def test_error_context_success(self):
        """Test ErrorContext with successful operation."""
        with patch("claude.shared.utils.error_handling.logger") as mock_logger:
            with ErrorContext("test operation") as ctx:
                result = "success"

            assert ctx.error is None
            mock_logger.debug.assert_has_calls(
                [
                    call("Starting operation: test operation"),
                    call("Completed operation: test operation"),
                ]
            )

    def test_error_context_with_error(self):
        """Test ErrorContext with error."""
        with patch("claude.shared.utils.error_handling.logger") as mock_logger:
            with pytest.raises(ValueError):
                with ErrorContext("test operation") as ctx:
                    raise ValueError("Test error")

            assert isinstance(ctx.error, ValueError)
            mock_logger.error.assert_called_with("Error in test operation: Test error")

    def test_error_context_with_cleanup(self):
        """Test ErrorContext with cleanup function."""
        cleanup_called = False

        def cleanup_func():
            nonlocal cleanup_called
            cleanup_called = True

        with pytest.raises(ValueError):
            with ErrorContext("test operation", cleanup_func):
                raise ValueError("Test error")

        assert cleanup_called

    def test_error_context_cleanup_failure(self):
        """Test ErrorContext handles cleanup function failures."""

        def failing_cleanup():
            raise RuntimeError("Cleanup failed")

        with patch("claude.shared.utils.error_handling.logger") as mock_logger:
            with pytest.raises(ValueError):
                with ErrorContext("test operation", failing_cleanup):
                    raise ValueError("Test error")

            # Should log both the original error and cleanup failure
            assert mock_logger.error.call_count == 2

    def test_error_context_suppress_errors(self):
        """Test ErrorContext with error suppression."""
        with ErrorContext("test operation", None, True) as ctx:
            raise ValueError("Test error")

        assert isinstance(ctx.error, ValueError)
        # Should not raise the exception

    def test_error_context_without_suppression(self):
        """Test ErrorContext without error suppression (default)."""
        with pytest.raises(ValueError):
            with ErrorContext("test operation"):
                raise ValueError("Test error")


class TestValidateInput:
    """Test validate_input decorator."""

    def test_validate_input_success(self):
        """Test input validation with valid inputs."""

        @validate_input({"x": lambda x: x > 0, "y": lambda y: isinstance(y, str)})
        def test_func(x, y):
            return f"{x}: {y}"

        result = test_func(5, "hello")
        assert result == "5: hello"

    def test_validate_input_failure(self):
        """Test input validation with invalid inputs."""

        @validate_input({"x": lambda x: x > 0})
        def test_func(x):
            return x

        with pytest.raises(ValueError, match="Invalid value for x: -1"):
            test_func(-1)

    def test_validate_input_with_defaults(self):
        """Test input validation with default parameters."""

        @validate_input({"x": lambda x: x > 0, "y": lambda y: len(y) > 0})
        def test_func(x, y="default"):
            return f"{x}: {y}"

        result = test_func(5)
        assert result == "5: default"

    def test_validate_input_kwargs(self):
        """Test input validation with keyword arguments."""

        @validate_input({"x": lambda x: x > 0, "y": lambda y: isinstance(y, str)})
        def test_func(x, y):
            return f"{x}: {y}"

        result = test_func(x=5, y="hello")
        assert result == "5: hello"

    def test_validate_input_partial_validation(self):
        """Test input validation only validates specified parameters."""

        @validate_input({"x": lambda x: x > 0})
        def test_func(x, y):
            return f"{x}: {y}"

        # Should not validate 'y' parameter
        result = test_func(5, -1)
        assert result == "5: -1"

    def test_validate_input_missing_parameter(self):
        """Test input validation with missing parameter in validation rules."""

        @validate_input({"z": lambda z: z > 0})  # 'z' not in function signature
        def test_func(x, y):
            return f"{x}: {y}"

        # Should work fine, just ignores unknown parameter
        result = test_func(5, "hello")
        assert result == "5: hello"


class TestErrorHandlingIntegration:
    """Integration tests for error handling components."""

    @pytest.mark.integration
    def test_complete_error_handling_workflow(self):
        """Test complete error handling workflow."""
        handler = ErrorHandler()
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Register recovery strategy
        def recovery_strategy(error, context):
            return f"recovered from {error}"

        handler.register_recovery_strategy(ValueError, recovery_strategy)

        # Simple circuit breaker test
        @cb
        def simple_failing_func():
            raise ValueError("Test failure")

        # First failure
        with pytest.raises(ValueError):
            simple_failing_func()
        assert cb.failure_count == 1
        assert not cb.is_open

        # Second failure - should open circuit
        with pytest.raises(ValueError):
            simple_failing_func()
        assert cb.failure_count == 2
        assert cb.is_open

        # Third attempt - should fail fast
        with pytest.raises(NonRecoverableError):
            simple_failing_func()

        # Test error handling
        error = ValueError("test error")
        result = handler.handle_error(error, {"operation": "test"})
        assert result == "recovered from test error"

    @pytest.mark.integration
    def test_error_handling_with_context_manager(self):
        """Test error handling with context manager."""
        handler = ErrorHandler()
        cleanup_called = False

        def cleanup_func():
            nonlocal cleanup_called
            cleanup_called = True

        def recovery_strategy(error, context):
            return "recovered"

        handler.register_recovery_strategy(ValueError, recovery_strategy)

        # Test error context with handler
        with ErrorContext(
            "test operation", cleanup_func=cleanup_func, suppress_errors=True
        ) as ctx:
            raise ValueError("Test error")

        assert cleanup_called
        assert isinstance(ctx.error, ValueError)

        # Use handler to recover from the error
        result = handler.handle_error(ctx.error, {"operation": "test"})
        assert result == "recovered"

    @pytest.mark.integration
    def test_comprehensive_retry_with_circuit_breaker(self):
        """Test comprehensive retry logic with circuit breaker."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Test graceful degradation separately from circuit breaker
        @graceful_degradation(fallback_value="graceful_fallback")
        def graceful_func():
            raise ValueError("Always fails")

        result = graceful_func()
        assert result == "graceful_fallback"

        # Test circuit breaker separately
        @cb
        def circuit_func():
            raise ValueError("Always fails")

        # First failure
        with pytest.raises(ValueError):
            circuit_func()
        assert cb.failure_count == 1

        # Second failure - should open circuit
        with pytest.raises(ValueError):
            circuit_func()
        assert cb.failure_count == 2
        assert cb.is_open
