"""Multi-Agent Supervisor for Question Normalization using LangGraph."""

import json
import logging
import os
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from config import get_settings
from .state import NormalizerState
from .prompts import (
    get_temporal_extraction_prompt,
    get_standardization_prompt,
    get_semantic_key_prompt
)

logger = logging.getLogger(__name__)


class QuestionNormalizer:
    """Multi-agent question normalizer using LangGraph."""

    def __init__(self, model: str = None):
        """
        Initialize question normalizer.

        Args:
            model: Model endpoint to use for normalization
                  If None, uses settings.serving_endpoint_name (default: databricks-gpt-5-4)
        """
        self.settings = get_settings()

        # Use model from settings if not provided
        if model is None:
            model = self.settings.serving_endpoint_name

        # Try to use Databricks Model Serving endpoint
        try:
            from langchain_community.chat_models import ChatDatabricks

            self.llm = ChatDatabricks(
                endpoint=model,
                temperature=0.0,  # Deterministic for caching
                max_tokens=1024
            )
            logger.info(f"Using Databricks Model Serving endpoint: {model}")

        except Exception as e:
            logger.warning(f"Could not initialize Databricks AI Gateway model: {e}")

            # Fallback to Anthropic if ANTHROPIC_API_KEY is set
            if os.getenv("ANTHROPIC_API_KEY"):
                from langchain_anthropic import ChatAnthropic

                self.llm = ChatAnthropic(
                    model="claude-sonnet-4-6",
                    temperature=0.0,
                    max_tokens=1024
                )
                logger.info("Using Anthropic Claude API")
            else:
                raise ValueError(
                    "No LLM available. Either:\n"
                    "1. Use Databricks AI Gateway, or\n"
                    "2. Set ANTHROPIC_API_KEY environment variable"
                )

        # Build LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine for normalization."""
        workflow = StateGraph(NormalizerState)

        # Add nodes
        workflow.add_node("extract_temporal", self._extract_temporal)
        workflow.add_node("standardize", self._standardize)
        workflow.add_node("generate_semantic_key", self._generate_semantic_key)

        # Define edges
        workflow.set_entry_point("extract_temporal")
        workflow.add_edge("extract_temporal", "standardize")
        workflow.add_edge("standardize", "generate_semantic_key")
        workflow.add_edge("generate_semantic_key", END)

        return workflow.compile()

    def _extract_temporal(self, state: NormalizerState) -> Dict[str, Any]:
        """
        Extract temporal references from question.

        Args:
            state: Current normalizer state

        Returns:
            Updated state with temporal_info
        """
        try:
            # Get prompt
            prompt = get_temporal_extraction_prompt(state.original_question)

            # Call LLM
            messages = [
                SystemMessage(content="You are a temporal extraction specialist. Output JSON only."),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)

            # Parse JSON response
            temporal_info = json.loads(response.content)

            logger.info(f"Temporal extraction: {temporal_info}")

            return {
                "temporal_info": temporal_info,
                "metadata": {
                    **state.metadata,
                    "temporal_extraction": "completed"
                }
            }

        except Exception as e:
            logger.error(f"Error extracting temporal info: {e}")
            return {
                "temporal_info": {"has_temporal": False},
                "metadata": {
                    **state.metadata,
                    "temporal_extraction": "failed",
                    "error": str(e)
                }
            }

    def _standardize(self, state: NormalizerState) -> Dict[str, Any]:
        """
        Standardize question for better cache hit ratio.

        Args:
            state: Current normalizer state

        Returns:
            Updated state with normalized_question
        """
        try:
            # Get prompt
            prompt = get_standardization_prompt(
                state.original_question,
                state.temporal_info or {}
            )

            # Call LLM
            messages = [
                SystemMessage(content="You are a question standardization specialist. Output JSON only."),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)

            # Parse JSON response
            result = json.loads(response.content)
            normalized_question = result.get("normalized_question", state.original_question)

            logger.info(f"Standardization: '{state.original_question}' → '{normalized_question}'")

            return {
                "normalized_question": normalized_question,
                "metadata": {
                    **state.metadata,
                    "standardization": "completed",
                    "changes_made": result.get("changes_made", [])
                }
            }

        except Exception as e:
            logger.error(f"Error standardizing question: {e}")
            return {
                "normalized_question": state.original_question,  # Fallback to original
                "metadata": {
                    **state.metadata,
                    "standardization": "failed",
                    "error": str(e)
                }
            }

    def _generate_semantic_key(self, state: NormalizerState) -> Dict[str, Any]:
        """
        Generate semantic key for caching.

        Args:
            state: Current normalizer state

        Returns:
            Updated state with semantic_key
        """
        try:
            # Get prompt
            prompt = get_semantic_key_prompt(
                state.normalized_question or state.original_question,
                state.temporal_info or {}
            )

            # Call LLM
            messages = [
                SystemMessage(content="You are a semantic key generation specialist. Output JSON only."),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)

            # Parse JSON response
            result = json.loads(response.content)
            semantic_key = result.get("semantic_key", "")

            logger.info(f"Semantic key: '{semantic_key}'")

            return {
                "semantic_key": semantic_key,
                "metadata": {
                    **state.metadata,
                    "semantic_key_generation": "completed",
                    "intent": result.get("intent"),
                    "entities": result.get("entities", []),
                    "confidence": result.get("confidence", 1.0)
                }
            }

        except Exception as e:
            logger.error(f"Error generating semantic key: {e}")
            return {
                "semantic_key": "",
                "metadata": {
                    **state.metadata,
                    "semantic_key_generation": "failed",
                    "error": str(e)
                }
            }

    def normalize(self, question: str) -> NormalizerState:
        """
        Normalize question through complete pipeline.

        Args:
            question: Original user question

        Returns:
            Final NormalizerState with normalized_question and semantic_key
        """
        # Create initial state
        initial_state = NormalizerState(
            original_question=question,
            metadata={"pipeline_started": True}
        )

        # Run through graph
        try:
            final_state = self.graph.invoke(initial_state)
            logger.info(
                f"Normalization complete: "
                f"'{question}' → '{final_state.get('normalized_question', question)}'"
            )
            return NormalizerState(**final_state)

        except Exception as e:
            logger.error(f"Error in normalization pipeline: {e}")
            # Return state with original question on failure
            return NormalizerState(
                original_question=question,
                normalized_question=question,
                temporal_info={"has_temporal": False},
                semantic_key="",
                metadata={"error": str(e)}
            )


# Global normalizer instance (singleton pattern)
_normalizer = None


def get_normalizer() -> QuestionNormalizer:
    """Get or create normalizer instance."""
    global _normalizer
    if _normalizer is None:
        _normalizer = QuestionNormalizer()
    return _normalizer


def normalize_question(question: str) -> NormalizerState:
    """
    Normalize a question using the global normalizer.

    Args:
        question: Original user question

    Returns:
        NormalizerState with normalization results
    """
    normalizer = get_normalizer()
    return normalizer.normalize(question)
