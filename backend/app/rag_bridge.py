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
        state = self._livekit_llm.visitor_state

        # ---- Visitor State Gate ----
        if state == "none":
            # No visitor confirmed — stay completely silent
            logger.info("RAGBridge: ignoring speech — visitor_state=none")
            return

        if state in ["asking", "asking_continue"]:
            # Robot asked "Are you there?" OR "Do you want to continue?"
            yes_words = [
                "yes", "yeah", "yep", "sure", "ok", "okay", "yea", "continue",
                "\u0646\u0639\u0645", "\u0622\u0647", "\u0623\u064a\u0648\u0647", "\u0627\u064a\u0648\u0647", "\u0627\u0647", "\u0623\u0647",
                "\u0637\u0628\u0639\u0627", "\u0645\u0648\u062c\u0648\u062f", "\u0643\u0645\u0644", "\u0645\u0627\u0634\u064a", "\u0627\u0643\u064a\u062f", "\u062d\u0627\u0636\u0631"
            ]
            no_words = [
                "no", "nope", "stop", "don't", "dont", "not now",
                "\u0644\u0627", "\u0644\u0623", "\u0644\u0627\u0621", "\u0645\u0634", "\u0645\u0634 \u0639\u0627\u064a\u0632", "\u0628\u0644\u0627\u0634", "\u0648\u0642\u0641"
            ]
            user_text = self._last_user_msg.lower().strip()
            confirmed = any(w in user_text for w in yes_words)
            declined = any(w in user_text for w in no_words)

            if confirmed:
                self._livekit_llm.visitor_state = "active"
                if state == "asking":
                    logger.info("RAGBridge: visitor confirmed presence — switching to active, sending greeting")
                    response_text = self._livekit_llm.greeting_text
                else:
                    logger.info("RAGBridge: visitor confirmed to continue — switching to active")
                    locale = self._livekit_llm.fixed_locale or "ar"
                    response_text = "\u062a\u0645\u0627\u0645\u060c \u0623\u0646\u0627 \u0645\u0639\u0627\u0643" if locale == "ar" else "Okay, I'm listening."

                self._event_ch.send_nowait(
                    llm.ChatChunk(
                        id=f"rag-{uuid.uuid4().hex}",
                        delta=llm.ChoiceDelta(content=response_text, role="assistant"),
                    )
                )
            elif declined:
                self._livekit_llm.visitor_state = "none"
                locale = self._livekit_llm.fixed_locale or "ar"
                response_text = "\u062a\u0645\u0627\u0645\u060c \u0647\u0633\u0643\u062a \u062f\u0644\u0648\u0642\u062a\u064a." if locale == "ar" else "Okay, I'll stop now."
                logger.info("RAGBridge: visitor declined — switching to none")
                self._event_ch.send_nowait(
                    llm.ChatChunk(
                        id=f"rag-{uuid.uuid4().hex}",
                        delta=llm.ChoiceDelta(content=response_text, role="assistant"),
                    )
                )
            else:
                # Not a confirmation — ask again politely
                locale = self._livekit_llm.fixed_locale or "ar"
                if state == "asking":
                    retry = "\u0647\u0644 \u0623\u0646\u062a \u0647\u0646\u0627\u061f" if locale == "ar" else "Are you still there?"
                else:
                    retry = "\u062a\u062d\u0628 \u0623\u0643\u0645\u0644\u061f" if locale == "ar" else "Do you want me to continue?"

                logger.info("RAGBridge: no confirmation received, asking again")
                self._event_ch.send_nowait(
                    llm.ChatChunk(
                        id=f"rag-{uuid.uuid4().hex}",
                        delta=llm.ChoiceDelta(content=retry, role="assistant"),
                    )
                )
            return  # Do not run RAG in this state

        # state == "active" — full RAG pipeline
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
                # If vision closes the gate mid-generation, immediately halt the stream.
                if self._livekit_llm.visitor_state != "active":
                    logger.info("RAGBridge: visitor no longer active. Halting stream.")
                    break

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
        # Visitor gate controlled by the vision loop:
        #   "none"             — no visitor, robot is completely silent
        #   "asking"           — person detected, robot asked if they want help
        #   "asking_continue"  — visitor looked away, robot asked whether to continue
        #   "active"           — visitor confirmed, full RAG conversation is enabled
        self.visitor_state: str = "none"
        self.greeting_text: str = ""   # set by agent.py after locale is resolved

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
