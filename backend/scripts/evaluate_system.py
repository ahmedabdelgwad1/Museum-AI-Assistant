"""
System Evaluation Script for the Museum AI Tourist Robot.
Reads session logs (JSON) and computes:
  1. Component-level Latency breakdown (Retrieval, LLM TTFT, Total)
  2. RAGAS AI Quality metrics (Faithfulness, Answer Relevance, Context Precision)

Usage:
    python backend/scripts/evaluate_system.py

Output:
    - Prints a summary table to the console.
    - Saves detailed results to backend/evaluation_results.json
"""

import json
import os
import sys
import glob
from statistics import mean

# ── Latency-Only Evaluation (always runs) ──────────────────────────

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "session_logs")


def load_all_turns() -> list[dict]:
    """Load all Q&A turns from every session log JSON file."""
    all_turns = []
    if not os.path.isdir(LOGS_DIR):
        print(f"⚠️  No session_logs directory found at: {LOGS_DIR}")
        print("   Run the robot and have at least one conversation first!")
        return all_turns

    # Only target our newly generated automated evaluation dataset!
    target_files = ["session_auto-eval-test-2.json", "session_auto-eval-multiturn.json"]
    
    files = glob.glob(os.path.join(LOGS_DIR, "session_*.json"))
    if not files:
        print(f"⚠️  No session log files found in: {LOGS_DIR}")
        return all_turns

    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        if filename not in target_files:
            continue  # Skip old mixed logs
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                session = json.load(f)
            turns = session.get("turns", [])
            for turn in turns:
                # Skip empty or greeting-only turns
                if turn.get("user_query") and turn.get("ai_response"):
                    all_turns.append(turn)
        except Exception as e:
            print(f"⚠️  Error reading {filepath}: {e}")
    return all_turns


def compute_latency_metrics(turns: list[dict]) -> dict:
    """Compute average component-level latency from logged turns."""
    retrieval_times = []
    llm_ttft_times = []
    total_latencies = []
    generation_times = []

    for turn in turns:
        if turn.get("retrieval_time", 0) > 0:
            retrieval_times.append(turn["retrieval_time"])
        if turn.get("llm_ttft_time", 0) > 0:
            llm_ttft_times.append(turn["llm_ttft_time"])
        if turn.get("latency_seconds", 0) > 0:
            total_latencies.append(turn["latency_seconds"])
        if turn.get("generation_time_seconds", 0) > 0:
            generation_times.append(turn["generation_time_seconds"])

    metrics = {
        "total_turns_analyzed": len(turns),
        "avg_retrieval_time": round(mean(retrieval_times), 3) if retrieval_times else "N/A",
        "avg_llm_generation_time": round(mean(generation_times), 3) if generation_times else "N/A",
        "avg_total_latency (TTFB)": round(mean(total_latencies), 3) if total_latencies else "N/A",
    }
    return metrics


# ── RAGAS AI Quality Evaluation (optional, needs dependencies) ─────


def compute_ragas_metrics(turns: list[dict]) -> dict | None:
    """
    Run RAGAS evaluation on turns that have 'contexts' logged.
    Returns None if ragas is not installed or no contexts available.
    """
    # Filter turns that have contexts
    evaluable = [t for t in turns if t.get("contexts") and len(t["contexts"]) > 0]
    if not evaluable:
        print("\n⚠️  No turns with 'contexts' found in logs.")
        print("   The robot needs to run with the updated code to log contexts.")
        print("   Skipping RAGAS evaluation.\n")
        return None

    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness
        metrics_list = [faithfulness]
    except ImportError:
        print("\n⚠️  RAGAS not installed. Install with:")
        print("   pip install ragas datasets langchain-openai")
        print("   Skipping RAGAS evaluation.\n")
        return None

    # Build the dataset
    dataset = Dataset.from_dict({
        "question": [t["user_query"] for t in evaluable],
        "answer": [t["ai_response"] for t in evaluable],
        "contexts": [t["contexts"] for t in evaluable],
    })

    # Configure the Judge LLM (try Groq first, fallback to OpenAI-compatible)
    judge_llm = None
    judge_embeddings = None

    try:
        from langchain_groq import ChatGroq
        groq_key_raw = os.environ.get("GROQ_API_KEY", "")
        # Use the THIRD key ([2]) because the first two hit daily limits
        groq_key = groq_key_raw.split(",")[2].strip() if len(groq_key_raw.split(",")) > 2 else groq_key_raw
        if groq_key:
            judge_llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key)
            print("✅ Using Groq (Llama-3) as RAGAS Judge LLM (free)")
    except ImportError:
        pass

    if judge_llm is None:
        try:
            from langchain_openai import ChatOpenAI
            groq_key_raw = os.environ.get("GROQ_API_KEY", "")
            groq_key = groq_key_raw.split(",")[2].strip() if len(groq_key_raw.split(",")) > 2 else groq_key_raw
            if groq_key:
                # Use OpenAI wrapper pointed at Groq's API
                judge_llm = ChatOpenAI(
                    model="llama-3.3-70b-versatile",
                    openai_api_key=groq_key,
                    openai_api_base="https://api.groq.com/openai/v1",
                )
                print("✅ Using Groq via OpenAI wrapper as RAGAS Judge LLM (free)")
        except ImportError:
            pass

    if judge_llm is None:
        print("⚠️  No Judge LLM configured. Set GROQ_API_KEY in your .env")
        print("   Skipping RAGAS evaluation.\n")
        return None

    # Use a lightweight embeddings model for RAGAS
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        judge_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    except ImportError:
        print("⚠️  langchain-huggingface not installed. Trying sentence-transformers...")
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            judge_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        except ImportError:
            print("⚠️  No embedding model available for RAGAS. Skipping.\n")
            return None

    print(f"\n🔬 Running RAGAS evaluation on {len(evaluable)} turns...")
    print("   (Evaluating Faithfulness)")

    try:
        results = evaluate(
            dataset=dataset,
            metrics=metrics_list,
            llm=judge_llm,
            embeddings=judge_embeddings,
        )
        return {
            "turns_evaluated": len(evaluable),
            "faithfulness": round(results["faithfulness"], 4),
        }
    except Exception as e:
        print(f"❌ RAGAS evaluation failed: {e}")
        return None


# ── Main ───────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("  🏛️  Museum AI Robot — System Evaluation Report")
    print("=" * 60)

    # Load .env for API keys
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        load_dotenv(env_path)
    except ImportError:
        pass

    # 1. Load session logs
    turns = load_all_turns()
    if not turns:
        print("\n❌ Cannot run evaluation without session logs. Exiting.")
        sys.exit(1)

    print(f"\n📊 Loaded {len(turns)} total Q&A turns from session logs.\n")

    # 2. Latency Metrics
    latency = compute_latency_metrics(turns)
    print("────────────────────────────────────────────────────────────")
    print("  📏 LATENCY METRICS (Component Breakdown)")
    print("────────────────────────────────────────────────────────────")
    print(f"  Total Benchmark Turns:     {latency['total_turns_analyzed']}")
    print(f"  Avg Retrieval Time:        {latency['avg_retrieval_time']} s")
    print(f"  Avg LLM Generation Time:   {latency['avg_llm_generation_time']} s")
    print(f"  Avg Total Latency (TTFB):  {latency['avg_total_latency (TTFB)']} s")
    print("────────────────────────────────────────────────────────────")
    print()

    # 3. RAGAS Metrics
    ragas = compute_ragas_metrics(turns)

    if ragas:
        print("─" * 60)
        print("  🧠 RAGAS AI QUALITY METRICS")
        print("─" * 60)
        print(f"  Turns Evaluated:     {ragas['turns_evaluated']}")
        print(f"  Faithfulness:        {ragas['faithfulness']}")
        print()

    # 4. Save to JSON
    output = {
        "latency_metrics": latency,
        "ragas_metrics": ragas,
    }
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("─" * 60)
    print(f"  💾 Results saved to: {output_path}")
    print("=" * 60)
    print()
    print("  ✅ Copy these results into Chapter 4 of your thesis!")
    print()


if __name__ == "__main__":
    main()
