"""
LiveKit Agent Worker for the Museum AI Tourist Robot.

Run with:
    python app/agent.py dev          # local development
    python app/agent.py start        # production

This process connects to a LiveKit room and handles:
    - VAD (Voice Activity Detection) via Silero
    - STT (Speech-to-Text) via Groq Whisper
    - RAG (Retrieval-Augmented Generation) via existing LangGraph pipeline
    - TTS (Text-to-Speech) via Groq
    - Interruption handling (user can speak while AI is talking)
"""
import logging

import os
import sys

# Add the backend directory to sys.path so 'app' module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, JobExecutorType
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions, RoomOutputOptions
from livekit.plugins import groq, silero

from app.rag_bridge import RAGBridge
from app.edge_tts_plugin import EdgeTTS
from app.utils.session_logger import SessionLogger

def prewarm_process(*args, **kwargs):
    """Load Heavy Models Before Session Starts to prevent 10s cold start"""
    from app.rag.embedder import get_embedder
    logger.info("Pre-warming Embeddings Model...")
    get_embedder()
    logger.info("Pre-warming Silero VAD...")
    silero.VAD.load()

load_dotenv()
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """Called once per room session — one session = one museum visitor."""

    logger.info("Agent starting for room: %s", ctx.room.name)

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    import json
    locale = "ar"
    if participant.metadata:
        try:
            metadata = json.loads(participant.metadata)
            locale = metadata.get("locale", "ar")
        except:
            pass

    logger.info("Participant joined with locale: %s", locale)

    if locale == "en":
        tts_voice = "en-US-JennyNeural"
        greeting = "Welcome to the Bibliotheca Alexandrina Antiquities Museum. You may ask me about any artifact."
    else:
        tts_voice = "ar-EG-SalmaNeural"
        greeting = "أهلاً وسهلاً بك في متحف الآثار بمكتبة الإسكندرية. يمكنك سؤالي عن أي قطعة أثرية."

    session_logger = SessionLogger(session_id=ctx.room.name, locale=locale)

    @ctx.room.on("disconnected")
    def on_disconnected(*args, **kwargs):
        session_logger.save()

    assistant = Agent(
        instructions="""أنت مرشد سياحي بشري ودود جداً في متحف الآثار اليونانية والرومانية بمكتبة الإسكندرية. 
مهمتك التحدث مع الزوار بطريقة آدمية، طبيعية، ودافئة جداً وكأنك إنسان حقيقي. 
إذا كنت تتحدث العربية، تحدث باللهجة المصرية العامية المبسطة والمثقفة لتبدو طبيعياً جداً، ولا تتحدث باللغة العربية الفصحى المعقدة.
إذا كنت تتحدث الإنجليزية، استخدم لغة محادثة طبيعية جداً وودية (Conversational, casual and very friendly English). 
تجنب تماماً الجمل الآلية أو الرسمية. استخدم أسلوب المحادثة الطبيعي، وكن مختصراً ومباشراً.""",
        vad=silero.VAD.load(
            min_silence_duration=0.5,      # seconds of silence before end-of-turn
            min_speech_duration=0.15,      # ignore short noises and hums shorter than 150ms
            prefix_padding_duration=0.2,   # include 200ms before detected speech
        ),

        # Speech-to-Text — Groq Whisper (same provider as before)
        stt=groq.STT(model="whisper-large-v3", language=locale),

        # LLM — our RAG bridge wrapping the existing LangGraph pipeline
        llm=RAGBridge(fixed_locale=locale, room=ctx.room, session_logger=session_logger),

        # Text-to-Speech — Edge TTS (Free & Reliable Arabic)
        tts=EdgeTTS(voice=tts_voice),

        # Interruption handling — user can speak to stop AI mid-sentence
        allow_interruptions=True,
    )

    # Start the assistant in the room
    session = AgentSession(
        allow_interruptions=True,
        min_interruption_duration=0.15,  # Needs only 0.15s of user speech to trigger barge-in
        min_interruption_words=0,
    )
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            text_enabled=True,
            audio_enabled=True,
            video_enabled=False,
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True,
            audio_enabled=True,
            sync_transcription=True,
        ),
    )

    # Greet the visitor on connection (in their selected language)
    await session.say(
        greeting,
        allow_interruptions=True,
    )

    logger.info("Agent ready and greeting sent.")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_process,
            initialize_process_timeout=60.0,   # PyTorch + sentence_transformers need ~15-20s to load
            job_executor_type=JobExecutorType.PROCESS,
        )
    )
