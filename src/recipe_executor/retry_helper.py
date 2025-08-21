"""Retry helper with exponential backoff for Recipe Executor."""

import time
import random
from typing import TypeVar, Callable, Optional, Any, Union, Type
from functools import wraps

T = TypeVar('T')


class RetryError(Exception):
    """Raised when all retry attempts fail."""
    
    def __init__(self, message: str, attempts: int, last_error: Optional[Exception] = None):
        """Initialize retry error with context.
        
        Args:
            message: Error message
            attempts: Number of attempts made
            last_error: The last exception that occurred
        """
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(message)


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that implements retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        exceptions: Exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            last_exception: Optional[Exception] = None
            
            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    attempt += 1
                    
                    if attempt > max_retries:
                        raise RetryError(
                            f"Failed after {attempt} attempts: {str(e)}",
                            attempts=attempt,
                            last_error=e
                        )
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    # Add jitter if enabled
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    # Log the retry attempt
                    print(f"Attempt {attempt} failed: {str(e)}")
                    print(f"Retrying in {delay:.2f} seconds...")
                    
                    time.sleep(delay)
            
            # This should never be reached, but for type safety
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry state")
        
        return wrapper
    return decorator


class RetryHelper:
    """Helper class for implementing retry logic with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize retry helper with configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delays
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def retry(
        self,
        func: Callable[..., T],
        *args: Any,
        exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
        **kwargs: Any
    ) -> T:
        """Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            exceptions: Exception types to catch and retry
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function
            
        Raises:
            RetryError: If all retry attempts fail
        """
        attempt = 0
        last_exception: Optional[Exception] = None
        
        while attempt <= self.max_retries:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                attempt += 1
                
                if attempt > self.max_retries:
                    raise RetryError(
                        f"Failed after {attempt} attempts: {str(e)}",
                        attempts=attempt,
                        last_error=e
                    )
                
                delay = self._calculate_delay(attempt)
                print(f"Attempt {attempt} failed: {str(e)}")
                print(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
        
        # This should never be reached, but for type safety
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry state")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff
        delay = min(
            self.base_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay
        )
        
        # Add jitter if enabled
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    async def retry_async(
        self,
        func: Callable[..., Any],
        *args: Any,
        exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
        **kwargs: Any
    ) -> Any:
        """Execute an async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            exceptions: Exception types to catch and retry
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function
            
        Raises:
            RetryError: If all retry attempts fail
        """
        import asyncio
        
        attempt = 0
        last_exception: Optional[Exception] = None
        
        while attempt <= self.max_retries:
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                attempt += 1
                
                if attempt > self.max_retries:
                    raise RetryError(
                        f"Failed after {attempt} attempts: {str(e)}",
                        attempts=attempt,
                        last_error=e
                    )
                
                delay = self._calculate_delay(attempt)
                print(f"Attempt {attempt} failed: {str(e)}")
                print(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
        
        # This should never be reached, but for type safety
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry state")