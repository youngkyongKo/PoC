"""Genie API module with retry logic."""

from .client import GenieClient, get_genie_client
from .retry_policy import (
    GenieAPIError,
    GenieRateLimitError,
    GenieServerError,
    with_retry,
    create_retry_decorator
)

__all__ = [
    # Client
    "GenieClient",
    "get_genie_client",
    # Errors
    "GenieAPIError",
    "GenieRateLimitError",
    "GenieServerError",
    # Retry
    "with_retry",
    "create_retry_decorator"
]
