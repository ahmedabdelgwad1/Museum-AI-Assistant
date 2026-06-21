"""
Three LangGraph node functions for the Corrective RAG pipeline:

  1. rewrite_query        — optimises the query for semantic search
  2. retrieve_and_grade   — retrieves artifacts + LLM-grades relevance
  3. generate_answer      — synthesises the final bilingual response
"""

import logging
import re
from typing import Any, Optional

from groq import Groq

from app.config import settings
from app.graph.state import GraphState
from app.graph.prompts import (
    get_rewrite_prompt,
    get_system_prompt,
    get_context_template,
    format_history_for_prompt,
    GRADE_PROMPT,
)
from app.rag.retriever import semantic_search
from app.utils.language import detect_language

logger = logging.getLogger(__name__)

# The delimiter the LLM is instructed to emit between spoken text and the action JSON.
# rag_bridge.py intercepts everything after this — it NEVER reaches TTS.
ROBOT_ACTION_DELIMITER = "---ROBOT_ACTION---"

# ---------------------------------------------------------------------------
# Shared Groq clients (one per API key, lazy-initialised)
# ---------------------------------------------------------------------------

_groq_clients: list[Groq] = []
_current_key_index: int = 0


def _get_clients() -> list[Groq]:
    global _groq_clients
    if not _groq_clients:
        keys = settings.groq_api_keys
        if not keys:
            raise ValueError("No GROQ_API_KEY configured.")
        _groq_clients = [Groq(api_key=k) for k in keys]
        logger.info("Initialised %d Groq client(s) for key rotation.", len(_groq_clients))
    return _groq_clients


def _llm_call(messages: list[dict], max_tokens: int = 512, temperature: float = 0.2, model: str = None, response_format: dict = None) -> str:
    """
    Thin wrapper around the Groq chat completions API with automatic
    API key rotation on RateLimitError (HTTP 429).
    Tries each configured key in order; raises if all keys are exhausted.
    """
    global _current_key_index
    from groq import RateLimitError

    clients = _get_clients()
    num_keys = len(clients)
    
    use_model = model or settings.llm_model

    for attempt in range(num_keys):
        idx = (_current_key_index + attempt) % num_keys
        client = clients[idx]
        try:
            kwargs = {
                "model": use_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format
                
            completion = client.chat.completions.create(**kwargs)
            _current_key_index = idx  # remember last working key
            return completion.choices[0].message.content or ""
        except RateLimitError as exc:
            logger.warning(
                "Rate limit hit on key #%d (%s). Trying next key...", idx, str(exc)[:80]
            )
            _current_key_index = (idx + 1) % num_keys  # advance to next key
        except Exception as exc:
            logger.error("Groq LLM call failed on key #%d: %s", idx, exc)
            raise

    # All keys exhausted
    logger.error("All %d Groq API key(s) are rate-limited.", num_keys)
    raise RuntimeError("All Groq API keys have reached their rate limit. Please try again later.")


# ---------------------------------------------------------------------------
# Node 1 — Query Rewriter
# ---------------------------------------------------------------------------


def rewrite_query(state: GraphState) -> GraphState:
    """
    Node 1 — Query Rewriter.

    - Detects the query language and sets ``language`` in state.
    - Calls the Groq LLM to rewrite the original query into a
      keyword-rich phrase optimised for vector search.
    - Increments ``rewrite_count`` on every pass (first pass sets it to 1).
    """
    query = state["original_query"]
    rewrite_count = state.get("rewrite_count", 0)

    # Detect language once (subsequent rewrites may already have it)
    lang = state.get("language") or detect_language(query)
    history = state.get("conversation_history") or []

    logger.info(
        "Rewriter [pass %d] | lang=%s | history=%d turns | query='%s'",
        rewrite_count + 1,
        lang,
        len(history),
        query[:80],
    )

    history_text = format_history_for_prompt(history)
    messages = [
        {
            "role": "user",
            "content": get_rewrite_prompt(lang).format(
                history=history_text,
                query=query,
            ),
        }
    ]

    try:
        rewritten = _llm_call(messages, max_tokens=80, temperature=0.1).strip()
    except Exception:
        # Fall back to the original query if the LLM call fails
        rewritten = query

    logger.info("Rewritten query: '%s'", rewritten[:80])

    return {
        **state,
        "rewritten_query": rewritten,
        "language": lang,
        "rewrite_count": rewrite_count + 1,
    }


# ---------------------------------------------------------------------------
# Node 2 — Retriever + Grader
# ---------------------------------------------------------------------------


def _summarise_docs(docs: list[dict]) -> str:
    """Build a compact summary of retrieved docs for the grader prompt."""
    if not docs:
        return "(no results)"
    lines = []
    for i, doc in enumerate(docs[:5], 1):  # cap at 5 for prompt length
        name = doc.get("artifact_name_en") or doc.get("artifact_name_ar") or "Unknown"
        hall = doc.get("hall_en", "")
        cat = doc.get("category_en", "")
        excerpt = doc.get("description_excerpt") or ""
        lines.append(f"{i}. {name} | Hall: {hall} | Category: {cat} | {excerpt[:100]}")
    return "\n".join(lines)


def retrieve_and_grade(state: GraphState) -> GraphState:
    """
    Node 2 — Retriever + Grader.

    - Runs semantic search in Supabase pgvector using the rewritten query.
    - Sets ``retrieved_docs`` in state.
    - Calls the Groq LLM to grade relevance.
    - Sets ``relevance_score`` in state.
    """
    query = state["rewritten_query"] or state["original_query"]
    logger.info("Retriever | query='%s'", query[:80])

    docs = semantic_search(query=query, top_k=settings.top_k_results)
    logger.info("Retrieved %d docs", len(docs))

    # Grade relevance
    summary = _summarise_docs(docs)
    messages = [
        {
            "role": "user",
            "content": GRADE_PROMPT.format(query=query, artifacts_summary=summary),
        }
    ]

    score = 0.0
    try:
        raw_score = _llm_call(messages, max_tokens=10, temperature=0.0).strip()
        # Extract the first float we find in the response
        match = re.search(r"\d+(\.\d+)?", raw_score)
        if match:
            score = min(1.0, max(0.0, float(match.group())))
    except Exception as exc:
        logger.warning("Grader LLM call failed, defaulting score=0.0: %s", exc)

    logger.info("Relevance score: %.2f", score)

    return {
        **state,
        "retrieved_docs": docs,
        "relevance_score": score,
    }


# ---------------------------------------------------------------------------
# Node 3 — Generator
# ---------------------------------------------------------------------------


def _build_artifact_context(docs: list[dict]) -> str:
    """Format retrieved artifact docs into a readable context block."""
    if not docs:
        return "(No relevant artifacts found)"
    parts = []
    for i, doc in enumerate(docs, 1):
        name_en = doc.get("artifact_name_en", "")
        name_ar = doc.get("artifact_name_ar", "")
        hall = doc.get("hall_en", "N/A")
        cat = doc.get("category_en", "N/A")
        site = doc.get("discovery_site_en", "N/A")
        desc = doc.get("description_en") or doc.get("description_ar") or ""
        link = doc.get("link", "")
        score = doc.get("relevance_score", "")

        block = [
            f"[{i}] {name_en} / {name_ar}",
            f"    Hall: {hall}",
            f"    Category: {cat}",
            f"    Discovery Site: {site}",
            f"    Description: {desc[:600]}",
        ]
        if link:
            block.append(f"    Link: {link}")
        if score:
            block.append(f"    Relevance: {score}")
        parts.append("\n".join(block))

    return "\n\n".join(parts)


def generate_answer(state: GraphState) -> GraphState:
    """
    Node 3 — Generator.

    Reached when:
      - relevance_score >= 0.5  (results are good enough), OR
      - rewrite_count >= max    (max retries exhausted → best-effort answer)

    Injects conversation_history (prior turns) into the message list so the
    LLM has full context of the ongoing conversation.
    Sets ``generation`` in state.
    """
    lang = state.get("language", "en")
    question = state["original_query"]
    docs = state.get("retrieved_docs", [])
    score = state.get("relevance_score", 0.0)
    rewrites = state.get("rewrite_count", 0)
    history = state.get("conversation_history") or []

    logger.info(
        "Generator | lang=%s | relevance=%.2f | rewrites=%d | docs=%d | history=%d turns",
        lang,
        score,
        rewrites,
        len(docs),
        len(history),
    )

    # Detect low-confidence retrieval: max rewrites used AND score still low
    low_confidence = score < settings.relevance_threshold and rewrites >= settings.max_rewrite_attempts
    vision_ctx = state.get("vision_context", "")

    system_prompt = get_system_prompt(lang, low_confidence=low_confidence, vision_context=vision_ctx)
    context = _build_artifact_context(docs)
    user_msg = get_context_template(lang).format(context=context, question=question)

    # Build messages: system → history (capped at last 6 turns) → current question
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # Sanitise and cap history to last 6 messages (3 exchanges)
    valid_roles = {"user", "assistant", "ai"}
    for turn in history[-6:]:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "ai":
            role = "assistant"
        if role in valid_roles and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_msg})

    try:
        answer = _llm_call(messages, max_tokens=1200, temperature=0.4)
    except Exception as exc:
        logger.error("Generator LLM call failed: %s", exc)
        answer = (
            "عذرًا، حدث خطأ أثناء إنشاء الإجابة. يرجى المحاولة مرة أخرى."
            if lang == "ar"
            else "I'm sorry, an error occurred while generating the answer. Please try again."
        )

    # ------------------------------------------------------------------
    # Split at the robot action delimiter to keep generation clean
    # ------------------------------------------------------------------
    robot_action = None
    if ROBOT_ACTION_DELIMITER in answer:
        spoken_part, _, action_part = answer.partition(ROBOT_ACTION_DELIMITER)
        answer = spoken_part.strip()
        try:
            import json
            # Strip markdown code fences if LLM wrapped JSON in them
            clean_json = action_part.strip().lstrip("`").rstrip("`")
            if clean_json.startswith("json"):
                clean_json = clean_json[4:].strip()
            robot_action = json.loads(clean_json)
            logger.info("Robot action parsed (sync): %s", robot_action)
        except Exception as parse_err:
            logger.warning("Failed to parse robot_action JSON: %s | raw=%s", parse_err, action_part[:200])
    else:
        # Fallback: regex search for JSON if the LLM forgot the delimiter
        import re, json
        match = re.search(r'\{[^{}]*"action"\s*:\s*"[^"]+"[^{}]*\}', answer)
        if match:
            try:
                robot_action = json.loads(match.group(0))
                # remove it from spoken answer
                answer = answer.replace(match.group(0), "").strip()
                logger.info("Robot action parsed via regex fallback (sync): %s", robot_action)
            except Exception:
                pass

    return {**state, "generation": answer, "robot_action": robot_action}


# ---------------------------------------------------------------------------
# Streaming Generator — used by /chat/stream (NOT part of the graph)
# ---------------------------------------------------------------------------


def generate_answer_stream(state: GraphState):
    """
    Streaming variant of generate_answer.

    Identical message construction, but calls Groq with stream=True and
    yields raw token strings one-by-one.  The caller is responsible for
    wrapping tokens in SSE format and accumulating the full text for TTS.

    Args:
        state: A fully-populated GraphState (output of retrieve_and_grade).

    Yields:
        str — each token delta from the Groq stream (may be empty string).
    """
    from groq import RateLimitError

    lang = state.get("language", "en")
    question = state["original_query"]
    docs = state.get("retrieved_docs", [])
    score = state.get("relevance_score", 0.0)
    rewrites = state.get("rewrite_count", 0)
    history = state.get("conversation_history") or []

    logger.info(
        "StreamGenerator | lang=%s | relevance=%.2f | rewrites=%d | docs=%d | history=%d turns",
        lang, score, rewrites, len(docs), len(history),
    )

    low_confidence = score < settings.relevance_threshold and rewrites >= settings.max_rewrite_attempts
    vision_ctx = state.get("vision_context", "")

    system_prompt = get_system_prompt(lang, low_confidence=low_confidence, vision_context=vision_ctx)
    context = _build_artifact_context(docs)
    user_msg = get_context_template(lang).format(context=context, question=question)

    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    valid_roles = {"user", "assistant", "ai"}
    for turn in history[-6:]:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "ai":
            role = "assistant"
        if role in valid_roles and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_msg})

    clients = _get_clients()
    global _current_key_index
    num_keys = len(clients)

    for attempt in range(num_keys):
        idx = (_current_key_index + attempt) % num_keys
        client = clients[idx]
        try:
            stream = client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.4,
                max_tokens=1200,
                stream=True,
            )
            _current_key_index = idx
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                yield delta
            return
        except RateLimitError as exc:
            logger.warning(
                "Stream rate limit on key #%d (%s). Trying next key...", idx, str(exc)[:80]
            )
            _current_key_index = (idx + 1) % num_keys
        except Exception as exc:
            logger.error("Stream LLM call failed on key #%d: %s", idx, exc)
            raise

    # All keys exhausted — yield an error message
    error_msg = (
        "عذرًا، النظام مشغول حالياً. يرجى المحاولة مرة أخرى بعد لحظات."
        if lang == "ar"
        else "Sorry, the system is busy. Please try again in a moment."
    )
    yield error_msg

async def generate_answer_stream_async(state: GraphState):
    from groq import AsyncGroq, RateLimitError
    import asyncio
    import json

    lang = state.get("language", "en")
    question = state["original_query"]
    docs = state.get("retrieved_docs", [])
    score = state.get("relevance_score", 0.0)
    rewrites = state.get("rewrite_count", 0)
    history = state.get("conversation_history") or []

    logger.info(
        "AsyncStreamGenerator | lang=%s | relevance=%.2f | rewrites=%d | docs=%d | history=%d turns",
        lang, score, rewrites, len(docs), len(history),
    )

    low_confidence = score < settings.relevance_threshold and rewrites >= settings.max_rewrite_attempts
    vision_ctx = state.get("vision_context", "")

    system_prompt = get_system_prompt(lang, low_confidence=low_confidence, vision_context=vision_ctx)
    context = _build_artifact_context(docs)
    user_msg = get_context_template(lang).format(context=context, question=question)

    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    valid_roles = {"user", "assistant", "ai"}
    for turn in history[-6:]:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "ai":
            role = "assistant"
        if role in valid_roles and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_msg})

    keys = settings.groq_api_keys
    num_keys = len(keys)
    global _current_key_index

    for attempt in range(num_keys):
        idx = (_current_key_index + attempt) % num_keys
        client = AsyncGroq(api_key=keys[idx])
        try:
            stream = await client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.4,
                max_tokens=1200,
                stream=True,
            )
            _current_key_index = idx

            # ------------------------------------------------------------------
            # Stream interception: collect tokens into a buffer.
            # Yield spoken text tokens normally; once the delimiter appears in
            # the buffer, stop yielding and silently accumulate the action JSON.
            # This keeps the TTS stream 100% clean.
            # ------------------------------------------------------------------
            buffer = ""
            delimiter_found = False
            action_buffer = ""

            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if not delta:
                    continue

                if delimiter_found:
                    # Past the delimiter — accumulate action JSON silently
                    action_buffer += delta
                    continue

                buffer += delta

                # Check if the delimiter appeared in the accumulated buffer
                if ROBOT_ACTION_DELIMITER in buffer:
                    delimiter_found = True
                    spoken_part, _, after = buffer.partition(ROBOT_ACTION_DELIMITER)
                    action_buffer = after  # any tokens already past delimiter
                    # Yield only the clean spoken text before the delimiter
                    if spoken_part:
                        yield spoken_part
                else:
                    # Safe to yield — no delimiter yet
                    # But hold back a window equal to delimiter length in case
                    # it's arriving split across chunks.
                    safe_len = max(0, len(buffer) - len(ROBOT_ACTION_DELIMITER))
                    if safe_len > 0:
                        yield buffer[:safe_len]
                        buffer = buffer[safe_len:]

            # Flush any remaining safe buffer (delimiter never arrived)
            if not delimiter_found and buffer:
                yield buffer

            # Parse and store the action on the mutable state dict
            if delimiter_found and action_buffer.strip():
                try:
                    clean_json = action_buffer.strip().lstrip("`").rstrip("`")
                    if clean_json.startswith("json"):
                        clean_json = clean_json[4:].strip()
                    parsed = json.loads(clean_json)
                    state["robot_action"] = parsed
                    logger.info("Robot action parsed (async): %s", parsed)
                except Exception as parse_err:
                    logger.warning(
                        "Failed to parse robot_action JSON: %s | raw=%s",
                        parse_err, action_buffer[:200]
                    )
                    state["robot_action"] = None
            else:
                # Fallback: maybe it's in the buffer without delimiter
                import re
                match = re.search(r'\{[^{}]*"action"\s*:\s*"[^"]+"[^{}]*\}', buffer)
                if match:
                    try:
                        parsed = json.loads(match.group(0))
                        state["robot_action"] = parsed
                        logger.info("Robot action parsed via regex fallback (async): %s", parsed)
                    except Exception:
                        state["robot_action"] = None
                else:
                    state["robot_action"] = None

            return
        except RateLimitError as exc:
            logger.warning(
                "Stream rate limit on key #%d (%s). Trying next key...", idx, str(exc)[:80]
            )
            _current_key_index = (idx + 1) % num_keys
        except Exception as exc:
            logger.error("Stream LLM call failed on key #%d: %s", idx, exc)
            raise

    # All keys exhausted
    state["robot_action"] = None
    error_msg = (
        "عذرًا، النظام مشغول حالياً. يرجى المحاولة مرة أخرى بعد لحظات."
        if lang == "ar"
        else "Sorry, the system is busy. Please try again in a moment."
    )
    yield error_msg
