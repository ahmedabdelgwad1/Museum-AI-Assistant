"""Builds and compiles the LangGraph Corrective RAG StateGraph."""

import logging

from langgraph.graph import StateGraph, END

from app.graph.state import GraphState
from app.graph.nodes import rewrite_query, retrieve_and_grade, generate_answer
from app.graph.edges import should_rewrite

logger = logging.getLogger(__name__)


def build_graph():
    """
    Assemble the 3-node Corrective RAG graph:

        rewriter ──► retriever ──┬──(relevance >= 0.5 OR rewrites >= 2)──► generator ──► END
                       ▲         │
                       └─────────┘  (relevance < 0.5 AND rewrites < 2 → retry)

    Returns a compiled LangGraph runnable.
    """
    graph = StateGraph(GraphState)

    # Register nodes
    graph.add_node("rewriter", rewrite_query)
    graph.add_node("retriever", retrieve_and_grade)
    graph.add_node("generator", generate_answer)

    # Entry point
    graph.set_entry_point("rewriter")

    # Fixed edge: rewriter → retriever
    graph.add_edge("rewriter", "retriever")

    # Conditional edge: retriever → rewriter (retry) | generator (proceed)
    graph.add_conditional_edges(
        "retriever",
        should_rewrite,
        {
            "rewrite": "rewriter",
            "generate": "generator",
        },
    )

    # Terminal edge: generator → END
    graph.add_edge("generator", END)

    compiled = graph.compile()
    logger.info("LangGraph Corrective RAG graph compiled successfully.")
    return compiled


# Module-level compiled graph — imported by routes
rag_graph = build_graph()
