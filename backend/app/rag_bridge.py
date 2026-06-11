"""
Wraps the existing LangGraph Corrective RAG pipeline as a LiveKit LLM plugin.
The LangGraph graph itself is untouched — this is a thin adapter only.
"""
import asyncio
import logging
import uuid
import time
from typing import Any

from livekit.agents import llm
from livekit.agents.types import (
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    NotGivenOr,
)

from app.graph.graph import rag_graph
from app.graph.state import GraphState
from app.utils.language import detect_language

logger = logging.getLogger(__name__)


class RAGStream(llm.LLMStream):
    """Yields a single chunk containing the full RAG answer."""

    def __init__(
        self,
        livekit_llm: "RAGBridge",
        chat_ctx: llm.ChatContext,
        *,
        tools: list | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        session_logger=None,
    ):
        super().__init__(
            livekit_llm,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
        )
        self.session_logger = session_logger
        self.start_time = time.time()

        # Extract the latest user message
        self._last_user_msg = ""
        for m in reversed(chat_ctx.messages()):
            if m.role == "user":
                self._last_user_msg = m.content if isinstance(m.content, str) else str(m.content)
                break

        # Build conversation history
        self._history: list[dict] = []
        for m in chat_ctx.messages()[:-1]:
            role = m.role if m.role in {"user", "assistant"} else "assistant"
            content = m.content if isinstance(m.content, str) else str(m.content)
            self._history.append({"role": role, "content": content})

        # Detect language (ar / en) from the user message
        if livekit_llm.fixed_locale:
            self._language = livekit_llm.fixed_locale
        else:
            detected = detect_language(self._last_user_msg)
            self._language = detected if detected in {"ar", "en"} else "ar"
        
        self._livekit_llm = livekit_llm

    async def _run(self) -> None:
        # Build initial GraphState for the RAG pipeline
        initial_state: GraphState = {
            "original_query": self._last_user_msg,
            "rewritten_query": "",
            "language": self._language,
            "retrieved_docs": [],
            "relevance_score": 0.0,
            "generation": "",
            "rewrite_count": 0,
            "conversation_history": self._history,
        }

        # Run the retrieval synchronously using existing node functions
        from app.graph.nodes import rewrite_query, retrieve_and_grade, generate_answer_stream_async
        from app.graph.edges import should_rewrite

        loop = asyncio.get_running_loop()
        try:
            # Step 1: Rewriter
            state = await loop.run_in_executor(None, lambda: rewrite_query(initial_state))
            # Step 2: Retriever & Grader
            state = await loop.run_in_executor(None, lambda: retrieve_and_grade(state))
            
            # Step 3: Conditional Loop
            while should_rewrite(state) == "rewrite":
                state = await loop.run_in_executor(None, lambda: rewrite_query(state))
                state = await loop.run_in_executor(None, lambda: retrieve_and_grade(state))
                
            # Step 4: Stream Generator
            full_answer = ""
            first_token_time = None
            async for chunk in generate_answer_stream_async(state):
                if chunk:
                    if first_token_time is None:
                        first_token_time = time.time()
                    full_answer += chunk
                    self._event_ch.send_nowait(
                        llm.ChatChunk(
                            id=f"rag-{uuid.uuid4().hex}",
                            delta=llm.ChoiceDelta(content=chunk, role="assistant"),
                        )
                    )
            
            # Log metrics
            if self.session_logger:
                end_time = time.time()
                latency = (first_token_time - self.start_time) if first_token_time else 0.0
                gen_time = end_time - self.start_time
                self.session_logger.add_turn(
                    user_query=self._last_user_msg,
                    ai_response=full_answer,
                    latency_seconds=latency,
                    generation_time_seconds=gen_time,
                    relevance_score=state.get("relevance_score", 0.0)
                )
        except Exception as exc:
            logger.exception("RAG streaming pipeline failed: %s", exc)
            error_msg = (
                "عذرًا، حدث خطأ أثناء معالجة سؤالك."
                if self._language == "ar"
                else "Sorry, an error occurred while processing your question."
            )
            self._event_ch.send_nowait(
                llm.ChatChunk(
                    id=f"rag-{uuid.uuid4().hex}",
                    delta=llm.ChoiceDelta(content=error_msg, role="assistant"),
                )
            )
            full_answer = error_msg

        # Check for goodbye
        text_lower = self._last_user_msg.lower().strip()
        end_words = ["thank you", "thanks", "شكرا", "شكرًا", "يعطيك العافية", "مع السلامة", "goodbye", "bye", "شكراً", "يعطيك العافيه", "باي"]
        if any(w in text_lower for w in end_words) and len(text_lower.split()) < 6:
            if self._livekit_llm.room:
                async def delayed_disconnect():
                    await asyncio.sleep(8)
                    try:
                        await self._livekit_llm.room.disconnect()
                    except:
                        pass
                asyncio.create_task(delayed_disconnect())


class RAGBridge(llm.LLM):
    """
    LiveKit LLM adapter that routes every user turn through the
    existing LangGraph Corrective RAG pipeline.
    """

    def __init__(self, fixed_locale: str | None = None, room=None, session_logger=None):
        super().__init__()
        self.fixed_locale = fixed_locale
        self.room = room
        self.session_logger = session_logger

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[Any] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> RAGStream:
        return RAGStream(
            self,
            chat_ctx=chat_ctx,
            tools=tools,
            conn_options=conn_options,
            session_logger=self.session_logger
        )
