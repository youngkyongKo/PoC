"""Genie API Client with retry logic."""

import logging
from typing import Optional, Dict, Any

from databricks.sdk import WorkspaceClient

from config import get_settings
from src.cache.models import GenieQueryResult
from .retry_policy import RetryableGenieClient, GenieAPIError

logger = logging.getLogger(__name__)


class GenieClient(RetryableGenieClient):
    """Client for Databricks Genie API with automatic retry."""

    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        """
        Initialize Genie client.

        Args:
            workspace_client: Databricks workspace client
        """
        super().__init__()
        self.settings = get_settings()
        self.w = workspace_client or WorkspaceClient()

    def ask(
        self,
        question: str,
        space_id: Optional[str] = None,
        timeout_seconds: int = 120
    ) -> GenieQueryResult:
        """
        Ask a question to Genie Space with retry logic.

        Args:
            question: Natural language question
            space_id: Genie Space ID (default: from settings)
            timeout_seconds: Timeout for query execution

        Returns:
            GenieQueryResult with SQL, data, and metadata

        Raises:
            GenieAPIError: If query fails after retries
        """
        space_id = space_id or self.settings.genie_space_id

        logger.info(f"Asking Genie: '{question[:50]}...'")

        # Call with retry
        def _ask():
            try:
                # Use MCP tool through SDK
                result = self.w.genie.ask_question(
                    space_id=space_id,
                    question=question,
                    timeout_seconds=timeout_seconds
                )

                # Check for errors
                self._handle_response_error(result)

                return result

            except Exception as e:
                logger.error(f"Genie API call failed: {e}")
                raise

        try:
            response = self._call_with_retry(_ask)

            # Parse response into GenieQueryResult
            result = GenieQueryResult(
                question=question,
                conversation_id=response.get('conversation_id'),
                message_id=response.get('message_id'),
                status=response.get('status', 'UNKNOWN'),
                sql=response.get('sql'),
                description=response.get('description'),
                columns=response.get('columns'),
                data=response.get('data'),
                row_count=response.get('row_count', 0),
                text_response=response.get('text_response'),
                error=response.get('error')
            )

            logger.info(
                f"Genie query completed: status={result.status}, "
                f"rows={result.row_count}"
            )

            return result

        except Exception as e:
            logger.error(f"Genie query failed: {e}")
            # Return error result
            return GenieQueryResult(
                question=question,
                status="FAILED",
                error=str(e)
            )

    def ask_followup(
        self,
        question: str,
        conversation_id: str,
        space_id: Optional[str] = None,
        timeout_seconds: int = 120
    ) -> GenieQueryResult:
        """
        Ask a follow-up question in existing conversation.

        Args:
            question: Follow-up question
            conversation_id: Conversation ID from previous query
            space_id: Genie Space ID (default: from settings)
            timeout_seconds: Timeout for query execution

        Returns:
            GenieQueryResult with SQL, data, and metadata

        Raises:
            GenieAPIError: If query fails after retries
        """
        space_id = space_id or self.settings.genie_space_id

        logger.info(
            f"Asking follow-up to conversation {conversation_id[:16]}...: "
            f"'{question[:50]}...'"
        )

        # Call with retry
        def _ask_followup():
            try:
                # Use MCP tool through SDK
                result = self.w.genie.ask_question_followup(
                    space_id=space_id,
                    conversation_id=conversation_id,
                    question=question,
                    timeout_seconds=timeout_seconds
                )

                # Check for errors
                self._handle_response_error(result)

                return result

            except Exception as e:
                logger.error(f"Genie follow-up API call failed: {e}")
                raise

        try:
            response = self._call_with_retry(_ask_followup)

            # Parse response into GenieQueryResult
            result = GenieQueryResult(
                question=question,
                conversation_id=response.get('conversation_id'),
                message_id=response.get('message_id'),
                status=response.get('status', 'UNKNOWN'),
                sql=response.get('sql'),
                description=response.get('description'),
                columns=response.get('columns'),
                data=response.get('data'),
                row_count=response.get('row_count', 0),
                text_response=response.get('text_response'),
                error=response.get('error')
            )

            logger.info(
                f"Genie follow-up completed: status={result.status}, "
                f"rows={result.row_count}"
            )

            return result

        except Exception as e:
            logger.error(f"Genie follow-up failed: {e}")
            # Return error result
            return GenieQueryResult(
                question=question,
                conversation_id=conversation_id,
                status="FAILED",
                error=str(e)
            )

    def _handle_response_error(self, response: Dict[str, Any]) -> None:
        """
        Override to handle Genie-specific response format.

        Args:
            response: Genie API response

        Raises:
            GenieAPIError: If response indicates error
        """
        status = response.get('status', '')

        if status == 'FAILED':
            error_msg = response.get('error', 'Unknown error')
            raise GenieAPIError(f"Genie query failed: {error_msg}")

        if status == 'CANCELLED':
            raise GenieAPIError("Genie query was cancelled")


# Global client instance (singleton pattern)
_genie_client = None


def get_genie_client() -> GenieClient:
    """Get or create Genie client instance."""
    global _genie_client
    if _genie_client is None:
        _genie_client = GenieClient()
    return _genie_client
