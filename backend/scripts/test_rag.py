#!/usr/bin/env python3
"""
CLI test script for the LangGraph Corrective RAG pipeline.

Usage:
    python scripts/test_rag.py
    python scripts/test_rag.py "Tell me about the Isis statuette"
    python scripts/test_rag.py "ما هي القطع المصنوعة من البرونز؟"
"""

import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Suppress verbose library logs; keep our own
logging.basicConfig(level=logging.WARNING)
logging.getLogger("app").setLevel(logging.INFO)

from app.rag.vectorstore import collection_count
from app.graph.graph import rag_graph
from app.graph.state import GraphState


def print_divider(char: str = "=", width: int = 72) -> None:
    print(char * width)


async def run_test(query: str) -> None:
    """Run a single query through the Corrective RAG graph and pretty-print results."""
    print_divider()
    print(f"QUERY       : {query}")
    print_divider("-")

    initial_state: GraphState = {
        "original_query": query,
        "rewritten_query": "",
        "language": "en",
        "retrieved_docs": [],
        "relevance_score": 0.0,
        "generation": "",
        "rewrite_count": 0,
    }

    result = await rag_graph.ainvoke(initial_state)

    print(f"LANGUAGE    : {result['language']}")
    print(f"REWRITES    : {result['rewrite_count']}")
    print(f"REWRITTEN Q : {result.get('rewritten_query', '')}")
    print(f"RELEVANCE   : {result.get('relevance_score', 0.0):.2f}")
    print(f"DOCS FOUND  : {len(result.get('retrieved_docs', []))}")
    print()
    print("ANSWER:")
    print(result["generation"])

    docs = result.get("retrieved_docs", [])
    if docs:
        print()
        print(f"TOP ARTIFACTS ({len(docs)}):")
        for i, doc in enumerate(docs, 1):
            name = doc.get("artifact_name_en") or doc.get("artifact_name_ar", "Unknown")
            hall = doc.get("hall_en", "N/A")
            score = doc.get("relevance_score", 0.0)
            link = doc.get("link", "")
            print(f"  {i}. [{score:.2f}] {name}")
            print(f"       Hall : {hall}")
            if link:
                print(f"       Link : {link}")

    print_divider()
    print()


async def main() -> None:
    count = collection_count()
    print(f"\n{'='*72}")
    print("  Bibliotheca Alexandrina Museum — Corrective RAG Test Suite")
    print(f"{'='*72}")
    print(f"  Supabase pgvector: {count} artifacts indexed")

    if count == 0:
        print("\n⚠️  Collection is empty!")
        print("   Run: python scripts/index_artifacts.py")
        return

    if len(sys.argv) > 1:
        queries = [" ".join(sys.argv[1:])]
    else:
        # Default test suite — mix of English and Arabic
        queries = [
            # English queries
            "Tell me about the bronze Isis statuette",
            "What artifacts were discovered in Saqqara?",
            "Show me funerary objects from the afterlife collection",
            "What are the museum's opening hours and location?",
            # Arabic queries
            "أخبرني عن تمثال إيمحتب",
            "ما هي القطع الأثرية المصنوعة من البرونز في المتحف؟",
            "ما هي الآثار المكتشفة في الكرنك؟",
        ]

    for q in queries:
        await run_test(q)


if __name__ == "__main__":
    asyncio.run(main())
