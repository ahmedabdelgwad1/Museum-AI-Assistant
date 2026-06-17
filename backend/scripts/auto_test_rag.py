"""
Automated RAG Testing Script.
Feeds pre-defined museum questions directly into the RAG pipeline
and logs the results (with contexts & timings) for RAGAS evaluation.

Usage:
    cd backend
    python scripts/auto_test_rag.py

This does NOT require LiveKit, microphone, or any voice components.
It talks directly to the RAG graph and saves results to session_logs/.
"""

import os
import sys
import time
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.graph.nodes import rewrite_query, retrieve_and_grade, generate_answer
from app.graph.edges import should_rewrite
from app.graph.state import GraphState
from app.utils.session_logger import SessionLogger

# ── Diverse Evaluation Dataset — 50 Questions across 8 Categories ─
# Based on REAL artifacts from Bibliotheca Alexandrina Antiquities Museum.

TEST_QUESTIONS = [
    # ── 1. Direct Factual — Arabic (10) ──────────────────────────────
    "قولي عن تمثال إيزيس وهي ترضع حربوقراط",
    "إيه هو تمثال إيمحتب اللي اتلقى في سقارة؟",
    "إيه هي المقلمة اللي فيها ستة أقلام بوص؟",
    "قولي عن تمثال الكتلة بتاع نس آمون ابن عنخ.إف",
    "إيه هو الزير اللي من عصر الدولة الحديثة من العمارنة؟",
    "قولي عن لوحة الألوان اللي اتلقت في مقابر أنطونيادس",
    "قولي عن تمثال الكتلة بتاع چد خنسو إيو.إف عنخ",
    "إيه هو الكاتب المصري القديم ومكانته الاجتماعية؟",
    "إيه هي أدوات الكاتب المصري القديم؟",
    "قولي عن خبيئة الكرنك وإزاي اتكتشفت؟",

    # ── 2. Direct Factual — English (10) ─────────────────────────────
    "Tell me about the statuette of Isis suckling Harpocrates",
    "What is the statuette of Imhotep found in Saqqara?",
    "Describe the pencase with six reed pens from ancient Egypt",
    "Tell me about the block statue of Nes-Amun from the Karnak Cache",
    "What is the blue-painted water jar from the Amarna Period?",
    "Tell me about the color palette found in the Antoniadis Tombs",
    "Describe the block statue of Djed Khonsu Iou.ef Ankh",
    "What was the role of scribes in ancient Egyptian society?",
    "What tools did Egyptian scribes use for writing?",
    "Tell me about the Karnak Cache and how it was discovered",

    # ── 3. Comparison Questions (5) ───────────────────────────────────
    "What is the difference between the block statue of Nes-Amun and Djed Khonsu Iou.ef Ankh?",
    "إيه الفرق بين تمثال إيمحتب وتمثال إيزيس من حيث الغرض الديني؟",
    "How do the writing tools (pencase) differ from the color palette in terms of usage?",
    "ما الفرق بين التماثيل الصغيرة (statuettes) والتماثيل الكاملة في المتحف؟",
    "Compare the symbolic meaning of colors in ancient Egyptian art versus their practical use",

    # ── 4. Multi-Retrieval Questions (5) ─────────────────────────────
    "Tell me about all the artifacts discovered in Saqqara in the museum",
    "What artifacts are displayed in showcase 2 of the Ancient Egyptian section?",
    "قولي عن كل القطع اللي في قسم الآثار المصرية القديمة",
    "What bronze artifacts does the museum have from the Late Period?",
    "اذكر كل القطع اللي ليها علاقة بالكتابة والكتبة في المتحف",

    # ── 5. Out-of-Scope Questions (5) ────────────────────────────────
    "What is the weather like today in Alexandria?",
    "إيه أحسن مطعم في الإسكندرية دلوقتي؟",
    "Can you book me a hotel room near the museum?",
    "ممكن تحجزلي تذكرة طيران لأسوان؟",
    "What is the latest iPhone model available in Egypt?",

    # ── 6. Conversational / Informal (5) ─────────────────────────────
    "يعني إيه الكلام اللي مكتوب على التمثال ده؟",
    "That bronze figurine looks cool, what's the story behind it?",
    "هو المتحف ده فيه حاجات فرعونية ولا يونانية بس؟",
    "ده التمثال الصغير ده مصنوع من إيه؟",
    "I see a statue of a woman holding a child, who is she?",

    # ── 7. Greetings & Social Interaction (5) ────────────────────────
    "أهلاً، ممكن تعرفني بالمتحف؟",
    "Hello, I just arrived at the museum, what should I see first?",
    "مرحباً، هل يمكنك مساعدتي في التعرف على المعروضات؟",
    "Hi there! I'm a student visiting for research, where do I start?",
    "صباح الخير، أنا زائر لأول مرة، إيه أهم القطع اللي لازم أشوفها؟",

    # ── 8. Thanks & Closing Interaction (5) ──────────────────────────
    "شكراً جزيلاً على المعلومات، استمتعت جداً بالزيارة",
    "Thank you so much, that was very informative!",
    "يعطيك العافية، هتكلمني عن قطعة تانية؟",
    "Thanks, I learned a lot today. Goodbye!",
    "مع السلامة، كانت تجربة رائعة",
]

# ── Multi-Turn Conversation Scenarios ─────────────────────────────
# Each scenario is a list of questions that build on each other.
# Tests if the RAG remembers context across turns (Chat History).

MULTI_TURN_SCENARIOS = [
    {
        "name": "Scenario A — Imhotep Deep Dive (Arabic)",
        "turns": [
            "قولي عن تمثال إيمحتب",
            "مين هو إيمحتب ده بالظبط؟",        # relies on previous answer
            "وامتى عاش تقريباً؟",              # needs context: Imhotep
            "وهل عندكم قطع تانية من نفس العصر ده؟",
        ],
    },
    {
        "name": "Scenario B — Isis Statuette (English)",
        "turns": [
            "Tell me about the statuette of Isis",
            "What material is it made of?",     # relies on context: bronze
            "Where was it found originally?",   # needs context
            "Are there similar pieces in the museum?",
        ],
    },
    {
        "name": "Scenario C — Scribes & Writing Tools (Mixed)",
        "turns": [
            "What did ancient Egyptian scribes do?",
            "What tools did they use?",         # relies on scribes context
            "قولي عن المقلمة اللي في المتحف",  # switch to Arabic mid-conversation
            "وهل الألوان دي موجودة لسه عندكم؟",
        ],
    },
]


def run_single_question(question: str, session_logger: SessionLogger) -> dict:
    """Run a single question through the full RAG pipeline."""
    from app.utils.language import detect_language

    lang = detect_language(question)

    initial_state: GraphState = {
        "original_query": question,
        "rewritten_query": "",
        "language": lang,
        "retrieved_docs": [],
        "relevance_score": 0.0,
        "generation": "",
        "rewrite_count": 0,
        "conversation_history": [],
    }

    start_time = time.time()

    # Step 1: Rewrite
    state = rewrite_query(initial_state)

    # Step 2: Retrieve & Grade (timed)
    retrieval_start = time.time()
    state = retrieve_and_grade(state)

    # Step 3: Conditional rewrite loop
    while should_rewrite(state) == "rewrite":
        state = rewrite_query(state)
        state = retrieve_and_grade(state)
    retrieval_time = time.time() - retrieval_start

    # Step 4: Generate answer (timed)
    llm_start = time.time()
    state = generate_answer(state)
    llm_time = time.time() - llm_start

    total_time = time.time() - start_time

    # Extract contexts
    contexts = []
    for doc in state.get("retrieved_docs", []):
        if isinstance(doc, dict):
            text = doc.get("description_en") or doc.get("description_ar") or ""
            name = doc.get("artifact_name_en") or doc.get("artifact_name_ar") or ""
            if text:
                contexts.append(f"{name}: {text[:500]}")
        elif hasattr(doc, "page_content"):
            contexts.append(doc.page_content)

    answer = state.get("generation", "")

    # Log to session logger
    session_logger.add_turn(
        user_query=question,
        ai_response=answer,
        latency_seconds=total_time,
        generation_time_seconds=total_time,
        relevance_score=state.get("relevance_score", 0.0),
        contexts=contexts,
        retrieval_time=retrieval_time,
        llm_ttft_time=llm_time,
    )

    return {
        "question": question,
        "answer": answer[:100] + "..." if len(answer) > 100 else answer,
        "relevance_score": state.get("relevance_score", 0.0),
        "retrieval_time": round(retrieval_time, 3),
        "llm_time": round(llm_time, 3),
        "total_time": round(total_time, 3),
        "num_contexts": len(contexts),
    }


def run_multi_turn_scenario(scenario: dict, session_logger: SessionLogger) -> list[dict]:
    """Run a multi-turn conversation scenario, passing history between turns."""
    from app.utils.language import detect_language

    print(f"\n  🔄 {scenario['name']}")
    history = []   # accumulates as conversation progresses
    results = []

    for turn_idx, question in enumerate(scenario["turns"], 1):
        print(f"     Turn {turn_idx}: {question[:60]}...", end=" ", flush=True)
        lang = detect_language(question)

        initial_state: GraphState = {
            "original_query": question,
            "rewritten_query": "",
            "language": lang,
            "retrieved_docs": [],
            "relevance_score": 0.0,
            "generation": "",
            "rewrite_count": 0,
            "conversation_history": history,  # ← pass accumulated history
        }

        try:
            start_time = time.time()
            state = rewrite_query(initial_state)
            state = retrieve_and_grade(state)
            while should_rewrite(state) == "rewrite":
                state = rewrite_query(state)
                state = retrieve_and_grade(state)
            state = generate_answer(state)
            total_time = time.time() - start_time

            answer = state.get("generation", "")

            # Append this turn to history for the next turn
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})

            # Extract contexts
            contexts = []
            for doc in state.get("retrieved_docs", []):
                if isinstance(doc, dict):
                    text = doc.get("description_en") or doc.get("description_ar") or ""
                    name = doc.get("artifact_name_en") or doc.get("artifact_name_ar") or ""
                    if text:
                        contexts.append(f"{name}: {text[:500]}")

            session_logger.add_turn(
                user_query=question,
                ai_response=answer,
                latency_seconds=total_time,
                generation_time_seconds=total_time,
                relevance_score=state.get("relevance_score", 0.0),
                contexts=contexts,
                retrieval_time=0.0,
                llm_ttft_time=total_time,
            )

            print(f"✅ ({total_time:.2f}s, relevance={state.get('relevance_score', 0.0):.2f})")
            results.append({"turn": turn_idx, "question": question, "answer": answer[:80], "time": total_time})

        except Exception as e:
            print(f"❌ {e}")

        if turn_idx < len(scenario["turns"]):
            time.sleep(5)

    return results


def main():
    print("=" * 60)
    print("  🤖 Automated RAG Testing — Museum AI Robot")
    print("=" * 60)
    print(f"\n  Running {len(TEST_QUESTIONS)} test questions...\n")

    session_logger = SessionLogger(session_id="auto-eval-test-2", locale="mixed")

    results = []
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "live_evaluation.html")

    def update_live_html(current_i, total_q, current_results):
        progress = int((current_i / total_q) * 100)
        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3">
    <title>Live Testing Dashboard - System Evaluation</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; margin: 0; padding: 40px; color: #333; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
        .progress-bar {{ width: 100%; background-color: #eee; border-radius: 8px; margin: 20px 0; overflow: hidden; }}
        .progress {{ width: {progress}%; height: 20px; background-color: #d4af37; transition: width 0.5s; }}
        .status {{ text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #7f8c8d; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: right; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f1f1f1; }}
        tr:hover {{ background-color: #f9f9f9; }}
        .tag {{ display: inline-block; background: #e1f5fe; color: #0288d1; padding: 3px 8px; border-radius: 4px; font-size: 12px; }}
        .tag-rel {{ background: #e8f5e9; color: #2e7d32; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>اختبار النظام المباشر (Live RAG Testing)</h1>
        <div class="status">جاري اختبار السؤال {current_i} من {total_q} ... ({progress}%)</div>
        <div class="progress-bar"><div class="progress"></div></div>
        
        <table>
            <thead>
                <tr>
                    <th width="30%">السؤال (Query)</th>
                    <th width="50%">إجابة النظام (AI Response)</th>
                    <th width="10%">الزمن</th>
                    <th width="10%">الموثوقية</th>
                </tr>
            </thead>
            <tbody>
"""
        for r in current_results[::-1]:  # Show newest first
            html += f"""
                <tr>
                    <td style="font-weight: bold; color: #d35400;">{r['question']}</td>
                    <td style="line-height: 1.6;">{r['answer']}</td>
                    <td><span class="tag">{r['total_time']}s</span></td>
                    <td><span class="tag tag-rel">{r['relevance_score']}</span></td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    # Initial empty dashboard
    update_live_html(0, len(TEST_QUESTIONS), results)
    print(f"  🌐 Open {html_path} in your browser to watch the live progress!\n")

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"  [{i}/{len(TEST_QUESTIONS)}] {question[:50]}...", end=" ", flush=True)
        try:
            result = run_single_question(question, session_logger)
            print(f"✅ ({result['total_time']}s, relevance={result['relevance_score']:.2f})")
            results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"question": question, "answer": f"Error: {e}", "total_time": 0, "relevance_score": 0})
        
        # Update dashboard
        update_live_html(i, len(TEST_QUESTIONS), results)

        # Delay to avoid Groq rate limiting
        time.sleep(12)

    # Save session
    session_logger.save()

    # ── Part 2: Multi-Turn Chat History Scenarios ──
    print("\n" + "=" * 60)
    print("  💬 MULTI-TURN CHAT HISTORY SCENARIOS")
    print("=" * 60)

    mt_logger = SessionLogger(session_id="auto-eval-multiturn", locale="mixed")
    for scenario in MULTI_TURN_SCENARIOS:
        run_multi_turn_scenario(scenario, mt_logger)
        time.sleep(5)
    mt_logger.save()
    print(f"  📁 Multi-turn session saved.")

    # Print summary
    print("\n" + "=" * 60)
    print("  📊 SINGLE-TURN SUMMARY")
    print("=" * 60)

    if results:
        avg_retrieval = sum(r["retrieval_time"] for r in results) / len(results)
        avg_llm = sum(r["llm_time"] for r in results) / len(results)
        avg_total = sum(r["total_time"] for r in results) / len(results)
        avg_relevance = sum(r["relevance_score"] for r in results) / len(results)

        print(f"  Questions Tested:      {len(results)}")
        print(f"  Avg Retrieval Time:    {avg_retrieval:.3f} s")
        print(f"  Avg LLM Time:          {avg_llm:.3f} s")
        print(f"  Avg Total Latency:     {avg_total:.3f} s")
        print(f"  Avg Relevance Score:   {avg_relevance:.2f}")
        print()
        print(f"  📁 Session saved to: backend/session_logs/session_auto-eval-test.json")
        print(f"  ➡️  Now run: python scripts/evaluate_system.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
