"""Retry policy with exponential backoff for Genie API."""

import logging
from typing import Callable, TypeVar, Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from config import get_settings

logger = logging.getLogger(__name__)

# Type variable for generic retry wrapper
T = TypeVar('T')


class GenieAPIError(Exception):
    """Base exception for Genie API errors."""
    pass


class GenieRateLimitError(GenieAPIError):
    """Exception raised when Genie API rate limit is hit (429)."""
    pass


class GenieServerError(GenieAPIError):
    """Exception raised when Genie API returns server error (5xx)."""
    pass


def should_retry_error(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.

    Args:
        exception: Exception to check

    Returns:
        True if should retry, False otherwise
    """
    # Retry on rate limit and server errors
    if isinstance(exception, (GenieRateLimitError, GenieServerError)):
        return True

    # Retry on HTTP errors (429, 5xx)
    if hasattr(exception, 'status_code'):
        status = getattr(exception, 'status_code')
        if status == 429 or (500 <= status < 600):
            return True

    return False


def create_retry_decorator(
    max_attempts: int = None,
    initial_delay: float = None,
    max_delay: float = None,
    multiplier: float = None
) -> Callable:
    """
    Create retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default: from settings)
        initial_delay: Initial delay in seconds (default: from settings)
        max_delay: Maximum delay in seconds (default: from settings)
        multiplier: Backoff multiplier (default: from settings)

    Returns:
        Retry decorator function
    """
    settings = get_settings()

    # Use settings defaults if not provided
    max_attempts = max_attempts or settings.genie_max_retries
    initial_delay = initial_delay or settings.genie_initial_delay
    max_delay = max_delay or settings.genie_max_delay
    multiplier = multiplier or settings.genie_backoff_multiplier

    logger.info(
        f"Retry policy: max_attempts={max_attempts}, "
        f"initial_delay={initial_delay}s, max_delay={max_delay}s, "
        f"multiplier={multiplier}"
    )

    return retry(
        # Stop after max attempts
        stop=stop_after_attempt(max_attempts),

        # Exponential backoff with jitter
        wait=wait_exponential(
            multiplier=initial_delay,
            max=max_delay,
            exp_base=multiplier
        ),

        # Retry on specific errors
        retry=retry_if_exception_type((
            GenieRateLimitError,
            GenieServerError
        )),

        # Logging
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )


def with_retry(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to add retry logic to a function.

    Usage:
        @with_retry
        def my_genie_call():
            # API call here
            pass

    Args:
        func: Function to wrap with retry logic

    Returns:
        Wrapped function with retry
    """
    retry_decorator = create_retry_decorator()
    return retry_decorator(func)


class RetryableGenieClient:
    """Mixin class providing retry capabilities for Genie API calls."""

    def __init__(self):
        """Initialize retryable client."""
        self.settings = get_settings()
        self._retry_decorator = create_retry_decorator()

    def _call_with_retry(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Call a function with retry logic.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function return value

        Raises:
            GenieAPIError: If all retries exhausted
        """
        # Wrap function with retry
        retryable_func = self._retry_decorator(func)

        try:
            return retryable_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"All retries exhausted: {e}")
            raise GenieAPIError(f"Genie API call failed after retries: {e}") from e

    def _handle_response_error(self, response: dict) -> None:
        """
        Check response for errors and raise appropriate exceptions.

        Args:
            response: API response dictionary

        Raises:
            GenieRateLimitError: If rate limit hit
            GenieServerError: If server error occurred
            GenieAPIError: For other API errors
        """
        # Check status field
        status = response.get('status', '')

        if status == 'FAILED':
            error_msg = response.get('error', 'Unknown error')

            # Check for rate limit
            if '429' in error_msg or 'rate limit' in error_msg.lower():
                raise GenieRateLimitError(f"Rate limit exceeded: {error_msg}")

            # Check for server error
            if '5' in str(response.get('status_code', '')) or 'server error' in error_msg.lower():
                raise GenieServerError(f"Server error: {error_msg}")

            # Generic API error
            raise GenieAPIError(f"API error: {error_msg}")


def get_retry_stats(func: Callable) -> dict:
    """
    Get retry statistics from a retryable function.

    Args:
        func: Function with retry decorator

    Returns:
        Dictionary with retry statistics
    """
    if hasattr(func, 'retry'):
        retry_state = func.retry
        return {
            "max_attempts": retry_state.stop.max_attempt_number if hasattr(retry_state.stop, 'max_attempt_number') else None,
            "attempts_made": getattr(func, '_attempts', 0)
        }
    return {}
