"""
LiveKit Agent Worker for the Museum AI Tourist Robot.

Run with:
    python app/agent.py dev          # local development
    python app/agent.py start        # production

This process connects to a LiveKit room and handles:
    - Vision (Face Detection + State Machine) via MediaPipe — hidden, server-side
    - VAD (Voice Activity Detection) via Silero
    - STT (Speech-to-Text) via Groq Whisper
    - RAG (Retrieval-Augmented Generation) via existing LangGraph pipeline
    - TTS (Text-to-Speech) via Edge-TTS
    - Interruption handling (user can speak while AI is talking)

Video streaming mode:
    - Frontend publishes camera track (silently, no preview shown to visitor)
    - Agent subscribes and analyzes frames via VisitorVision at ~10 FPS
    - Greeting is sent ONLY when visitor looks at the robot (ENGAGED state)
    - Microphone is muted when visitor leaves (IDLE state)
"""
import logging
import asyncio
import json
import os
import sys

import numpy as np
import cv2

# Add the backend directory to sys.path so 'app' module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, JobExecutorType
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions, RoomOutputOptions
from livekit.plugins import groq, silero

from app.rag_bridge import RAGBridge
from app.edge_tts_plugin import EdgeTTS
from app.utils.session_logger import SessionLogger
from app.vision import VisitorVision


def prewarm_process(*args, **kwargs):
    """Load heavy models at worker startup to eliminate cold-start latency."""
    from app.rag.embedder import get_embedder
    logger.info("Pre-warming Embeddings Model...")
    get_embedder()
    logger.info("Pre-warming Silero VAD...")
    silero.VAD.load()
    logger.info("Pre-warming MediaPipe FaceMesh...")
    # Instantiate and immediately close — loads .so libraries into memory
    v = VisitorVision()
    v.close()
    logger.info("Prewarm complete ✅")


load_dotenv()
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Video processing loop — runs as a background asyncio Task           #
# ------------------------------------------------------------------ #

async def _vision_loop(
    track: rtc.VideoTrack,
    vision: VisitorVision,
    session: AgentSession,
    greeting: str,
):
    """
    Continuously reads video frames from the LiveKit track and passes them
    to VisitorVision.process_frame() (via asyncio.to_thread so it never
    blocks the event loop).

    Drives the greeting and microphone-gate logic based on vision state.
    """
    greeted = False
    prev_state = "IDLE"

    video_stream = rtc.VideoStream(track=track, format=rtc.VideoBufferType.BGRA)

    async for frame_event in video_stream:
        frame = frame_event.frame

        # Convert LiveKit BGRA buffer → numpy BGR (drop alpha channel)
        arr  = np.frombuffer(frame.data, dtype=np.uint8).reshape((frame.height, frame.width, 4))
        bgr  = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

        # Process frame in a thread — non-blocking, MediaPipe releases GIL
        new_state = await asyncio.to_thread(vision.process_frame, bgr)

        if new_state == prev_state:
            continue  # No transition — nothing to act on
        prev_state = new_state

        # ---- State transition actions ----
        if new_state == "ENGAGED" and not greeted:
            logger.info("Vision ENGAGED → sending greeting and enabling mic")
            greeted = True
            # Enable microphone so the visitor's voice is processed
            await session.set_audio_enabled(True)
            await session.say(greeting, allow_interruptions=True)

        elif new_state == "IDLE" and greeted:
            logger.info("Vision IDLE → visitor left, muting mic and resetting session")
            greeted = False
            # Mute microphone — ignore stray audio when no visitor is present
            await session.set_audio_enabled(False)
            vision.reset()


# ------------------------------------------------------------------ #
# Agent entrypoint                                                     #
# ------------------------------------------------------------------ #

async def entrypoint(ctx: JobContext):
    """Called once per room session — one session = one museum visitor."""

    logger.info("Agent starting for room: %s", ctx.room.name)

    # Subscribe to BOTH audio and video tracks from the participant
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    participant = await ctx.wait_for_participant()

    locale = "ar"
    if participant.metadata:
        try:
            metadata = json.loads(participant.metadata)
            locale = metadata.get("locale", "ar")
        except Exception:
            pass

    logger.info("Participant joined with locale: %s", locale)

    if locale == "en":
        tts_voice = "en-US-JennyNeural"
        greeting  = (
            "Welcome to the Bibliotheca Alexandrina Antiquities Museum. "
            "You may ask me about any artifact."
        )
    else:
        tts_voice = "ar-EG-SalmaNeural"
        greeting  = (
            "أهلاً وسهلاً بك في متحف الآثار بمكتبة الإسكندرية. "
            "يمكنك سؤالي عن أي قطعة أثرية."
        )

    session_logger = SessionLogger(session_id=ctx.room.name, locale=locale)

    @ctx.room.on("disconnected")
    def on_disconnected(*args, **kwargs):
        session_logger.save()

    # ---- Build Agent ----
    assistant = Agent(
        instructions=(
            "أنت مرشد سياحي بشري ودود جداً في متحف الآثار اليونانية والرومانية بمكتبة الإسكندرية. "
            "مهمتك التحدث مع الزوار بطريقة آدمية، طبيعية، ودافئة جداً وكأنك إنسان حقيقي. "
            "إذا كنت تتحدث العربية، تحدث باللهجة المصرية العامية المبسطة والمثقفة لتبدو طبيعياً جداً. "
            "إذا كنت تتحدث الإنجليزية، استخدم لغة محادثة طبيعية جداً وودية. "
            "تجنب تماماً الجمل الآلية أو الرسمية. وكن مختصراً ومباشراً."
        ),
        vad=silero.VAD.load(
            min_silence_duration=0.5,
            min_speech_duration=0.15,
            prefix_padding_duration=0.2,
        ),
        stt=groq.STT(model="whisper-large-v3", language=locale),
        llm=RAGBridge(fixed_locale=locale, room=ctx.room, session_logger=session_logger),
        tts=EdgeTTS(voice=tts_voice),
        allow_interruptions=True,
    )

    # ---- Start session with mic initially MUTED (vision will unmute it) ----
    session = AgentSession(
        allow_interruptions=True,
        min_interruption_duration=0.15,
        min_interruption_words=0,
    )
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            text_enabled=True,
            audio_enabled=False,   # ← starts muted; vision loop enables when ENGAGED
            video_enabled=False,   # agent does not need to output video
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True,
            audio_enabled=True,
            sync_transcription=True,
        ),
    )

    # ---- Vision: hook into video track when it arrives ----
    vision = VisitorVision()

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            logger.info("Video track subscribed from %s — starting vision loop", participant.identity)
            asyncio.ensure_future(
                _vision_loop(track, vision, session, greeting)
            )

    # ---- Cleanup vision on disconnect ----
    @ctx.room.on("disconnected")
    def on_room_disconnected(*args, **kwargs):
        vision.close()

    logger.info(
        "Agent ready — waiting for visitor to look at the robot before greeting."
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_process,
            initialize_process_timeout=60.0,
            job_executor_type=JobExecutorType.PROCESS,
        )
    )
