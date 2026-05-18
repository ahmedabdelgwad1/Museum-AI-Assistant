"""Conditional edge logic for the LangGraph Corrective RAG pipeline."""

from app.config import settings
from app.graph.state import GraphState


def should_rewrite(state: GraphState) -> str:
    """
    Routing function called after the retriever/grader node.

    Decision logic:
    - If relevance_score < 0.5 AND rewrite_count < settings.max_rewrite_attempts
      → return "rewrite" (rewriter generates a better query and retrieval is retried)
    - Otherwise → return "generate"
      (results are relevant enough, or max rewrites exhausted)

    Returns:
        "rewrite" or "generate" — matched against the conditional edges map
        in graph.py.
    """
    score = state.get("relevance_score", 0.0)
    rewrites_done = state.get("rewrite_count", 0)

    if score < settings.relevance_threshold and rewrites_done < settings.max_rewrite_attempts:
        return "rewrite"
    return "generate"
