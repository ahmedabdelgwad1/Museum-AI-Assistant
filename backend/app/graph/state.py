"""Shared state TypedDict for the LangGraph Corrective RAG pipeline."""

from typing import TypedDict, List, Dict


class GraphState(TypedDict):
    """
    State shared across all nodes in the Corrective RAG graph.

    Fields:
        original_query:       The raw user query — never modified after initial set.
        rewritten_query:      Optimised search query produced by the rewriter node.
        language:             Detected language — 'ar' or 'en'.
        retrieved_docs:       List of artifact dicts returned from semantic search.
        relevance_score:      Float 0.0–1.0 assigned by the grader LLM call.
        generation:           Final answer string produced by the generator node.
        rewrite_count:        Tracks how many query-rewrites have occurred (max 2).
        conversation_history: Prior conversation turns [{"role": ..., "content": ...}].
                              Injected into the generator to maintain context.
    """

    original_query: str
    rewritten_query: str
    language: str
    retrieved_docs: List[dict]
    relevance_score: float
    generation: str
    rewrite_count: int
    conversation_history: List[Dict[str, str]]
    vision_context: str
