"""
LiveKit Agent Worker for the Museum AI Tourist Robot.

Run with:
    python app/agent.py dev          # local development
    python app/agent.py start        # production

This process connects to a LiveKit room and handles:
    - Vision (Face Detection + State Machine) via OpenCV Haar Cascade — hidden, server-side
    - VAD (Voice Activity Detection) via Silero
    - STT (Speech-to-Text) via Groq Whisper
    - RAG (Retrieval-Augmented Generation) via existing LangGraph pipeline
    - TTS (Text-to-Speech) via Edge-TTS
    - Interruption handling (user can speak while AI is talking)

Video streaming mode:
    - Frontend publishes camera track (silently, no preview shown to visitor)
    - Agent subscribes and analyzes frames via VisitorVision at ~10 FPS
    - Greeting is sent ONLY when visitor looks at the robot (ENGAGED state)
    - Conversation is gated by vision state and interrupted when visitor leaves
"""
import logging
import asyncio
import json
import os
import sys
from typing import Any

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


def prewarm_process(*args, **kwargs):
    """Load heavy models at worker startup to eliminate cold-start latency."""
    from app.rag.embedder import get_embedder
    logger.info("Pre-warming Embeddings Model...")
    get_embedder()
    logger.info("Pre-warming Silero VAD...")
    silero.VAD.load()
    logger.info("Prewarm complete ✅")


load_dotenv()
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Video processing loop — runs as a background asyncio Task           #
# ------------------------------------------------------------------ #

async def _vision_loop(
    track: rtc.VideoTrack,
    vision: Any,
    session: AgentSession,
    rag_bridge: "RAGBridge",
    question: str,
    continue_question: str,
):
    asked = False
    prev_state = "IDLE"
    timeout_handle: asyncio.Task | None = None
    ask_task: Any = None
    frame_count = 0

    video_stream = rtc.VideoStream(track=track, format=rtc.VideoBufferType.BGRA)

    async def interrupt_current_speech() -> None:
        nonlocal ask_task
        try:
            logger.info("Vision: >>> INTERRUPTING SPEECH <<<")
            if ask_task:
                if hasattr(ask_task, "interrupt"):
                    ask_task.interrupt()
                elif hasattr(ask_task, "cancel"):
                    ask_task.cancel()
                ask_task = None
            try:
                result = session.interrupt(force=True)
                # Handle both sync and async interrupt implementations
                if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                    await result
                logger.info("Vision: speech interrupted successfully")
            except RuntimeError as re:
                if "isn't running" in str(re):
                    logger.warning("Vision: could not interrupt, AgentSession is not running")
                else:
                    raise
        except Exception:
            logger.exception("Vision: failed to interrupt session")

    async def close_gate(reason: str, *, reset_vision: bool = False) -> None:
        nonlocal asked
        logger.info("Vision %s → closing speech gate + interrupting", reason)
        asked = False
        rag_bridge.visitor_state = "none"
        await interrupt_current_speech()
        if reset_vision:
            vision.reset()

    async def close_after_continue_timeout() -> None:
        await asyncio.sleep(3.0)
        if rag_bridge.visitor_state == "asking_continue":
            await close_gate("continue timeout", reset_vision=True)

    async def ask_to_continue() -> None:
        nonlocal timeout_handle, ask_task
        logger.info("Vision OBSERVING → visitor looked away, asking to continue")
        rag_bridge.visitor_state = "asking_continue"
        await interrupt_current_speech()
        if timeout_handle:
            timeout_handle.cancel()
        try:
            ask_task = session.say(continue_question, allow_interruptions=True)
        except RuntimeError as re:
            if "isn't running" in str(re):
                logger.warning("Vision: could not speak continue question, AgentSession is not running")
            else:
                raise
        timeout_handle = asyncio.create_task(close_after_continue_timeout())

    try:
        async for frame_event in video_stream:
            frame = frame_event.frame
            arr = np.frombuffer(frame.data, dtype=np.uint8).reshape((frame.height, frame.width, 4))
            bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

            new_state = await asyncio.to_thread(vision.process_frame, bgr)

            # Periodic health log every ~3 seconds (30 frames @ 10fps)
            frame_count += 1
            if frame_count % 30 == 0:
                logger.info(
                    "Vision loop alive: vision_state=%s, visitor_gate=%s, absence=%d, look_away=%d",
                    new_state, rag_bridge.visitor_state,
                    vision._stable_absence, vision._look_away_frames,
                )

            if new_state == prev_state:
                continue
            prev_state = new_state

            logger.info("Vision state changed → %s (visitor_gate=%s)", new_state, rag_bridge.visitor_state)

            # ---- ENGAGED: visitor is centered and can be spoken to ----
            if new_state == "ENGAGED":
                if timeout_handle:
                    timeout_handle.cancel()
                    timeout_handle = None

                # Trigger DINOv2 visual recognition
                try:
                    from app.dinov2 import DinoV2Encoder
                    from app.rag.vectorstore import get_supabase_client
                    from PIL import Image
                    import json
                    
                    encoder = DinoV2Encoder.get_instance()
                    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb)
                    visual_vec = encoder.embed(pil_img)
                    
                    if visual_vec:
                        client = get_supabase_client()
                        response = client.rpc(
                            "match_visual_artifacts",
                            {
                                "query_embedding": visual_vec,
                                "match_threshold": 0.35,
                                "match_count": 1
                            }
                        ).execute()
                        if response.data:
                            matched = response.data[0]
                            meta = matched.get("metadata", {})
                            if isinstance(meta, str):
                                try:
                                    meta = json.loads(meta)
                                except:
                                    pass
                            
                            art_name_en = meta.get('artifact_name_en', 'Unknown')
                            art_name_ar = meta.get('artifact_name_ar', 'غير معروف')
                            desc_en = meta.get('description_en', '')
                            desc_ar = meta.get('description_ar', '')
                            rag_bridge.vision_context = f"EN: The visitor is looking at: {art_name_en}. Description: {desc_en} | AR: الزائر ينظر إلى: {art_name_ar}. الوصف: {desc_ar}"
                            logger.info("Vision matched artifact: %s", art_name_en)
                        else:
                            rag_bridge.vision_context = ""
                except Exception as e:
                    logger.error("Failed to run DINOv2 visual match: %s", e)

                if rag_bridge.visitor_state == "asking_continue":
                    logger.info("Vision ENGAGED → visitor looked back, resuming")
                    rag_bridge.visitor_state = "active"
                elif rag_bridge.visitor_state == "none" and not asked:
                    logger.info("Vision ENGAGED → asking visitor to opt in")
                    asked = True
                    rag_bridge.visitor_state = "asking"
                    try:
                        ask_task = session.say(question, allow_interruptions=True)
                    except RuntimeError as re:
                        if "isn't running" in str(re):
                            logger.warning("Vision: could not speak opt-in greeting, AgentSession is not running")
                            asked = False
                            rag_bridge.visitor_state = "none"
                        else:
                            raise

            # ---- OBSERVING: visible but looking away/not centered ----
            elif new_state == "OBSERVING":
                if rag_bridge.visitor_state == "active":
                    await ask_to_continue()
                elif rag_bridge.visitor_state == "asking":
                    await close_gate("visitor looked away before confirming")

            # ---- IDLE: visitor walked away completely ----
            elif new_state == "IDLE" and (asked or rag_bridge.visitor_state != "none"):
                if timeout_handle:
                    timeout_handle.cancel()
                    timeout_handle = None
                await close_gate("IDLE", reset_vision=True)
    except Exception as e:
        logger.exception("Vision loop crashed unexpectedly!")



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
        question  = "Welcome to the Antiquities Museum! Would you like to learn about the artifacts?"
        continue_question = "Do you want me to continue?"
        greeting  = "Great! Feel free to ask me about any piece you see."
    else:
        tts_voice = "ar-EG-SalmaNeural"
        question  = "أهلاً بك في متحف الآثار! تحب أكلمك عن القطع الأثرية؟"
        continue_question = "تحب أكمل؟"
        greeting  = "عظيم! تقدر تسألني عن أي قطعة أثرية لفتت انتباهك."

    session_logger = SessionLogger(session_id=ctx.room.name, locale=locale)

    @ctx.room.on("disconnected")
    def on_disconnected(*args, **kwargs):
        session_logger.save()

    # Ensure GROQ_API_KEY is a single key (not comma-separated list) for LiveKit plugins
    from app.config import settings
    if settings.groq_api_keys:
        os.environ["GROQ_API_KEY"] = settings.groq_api_keys[0]

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
        llm=(rag_bridge := RAGBridge(fixed_locale=locale, room=ctx.room, session_logger=session_logger)),
        tts=EdgeTTS(voice=tts_voice),
        allow_interruptions=True,
    )
    rag_bridge.greeting_text = greeting  # used by RAGBridge when visitor confirms "yes"

    # ---- Start session ----
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
            audio_enabled=True,    # mic always active; greeting is gated by vision
            video_enabled=False,   # agent does not output video
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True,
            audio_enabled=True,
            sync_transcription=True,
        ),
    )

    # ---- Vision: hook into video track when it arrives ----
    bypass_vision = os.getenv("BYPASS_VISION", "false").lower() == "true"
    if bypass_vision:
        vision = None
    else:
        from app.vision import VisitorVision
        vision = VisitorVision()

    vision_task: asyncio.Task | None = None
    video_track_received = asyncio.Event()

    def start_vision_loop(
        track: rtc.Track,
        participant: rtc.RemoteParticipant,
    ) -> None:
        nonlocal vision_task
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            if vision_task and not vision_task.done():
                return
            if vision is None:
                return
            logger.info("Video track subscribed from %s — starting vision loop", participant.identity)
            video_track_received.set()
            vision_task = asyncio.ensure_future(
                _vision_loop(track, vision, session, rag_bridge, question, continue_question)
            )

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logger.info("Track subscribed: kind=%s, name=%s", track.kind, track.name)
        start_vision_loop(track, participant)

    for publication in participant.track_publications.values():
        if publication.track is not None:
            logger.info("Existing track found: kind=%s, name=%s", publication.kind, getattr(publication.track, 'name', 'unknown'))
        if publication.kind == rtc.TrackKind.KIND_VIDEO and publication.track is not None:
            start_vision_loop(publication.track, participant)

    async def check_video_timeout():
        try:
            await asyncio.wait_for(video_track_received.wait(), timeout=3.0)
            logger.info("Video track received successfully. Vision-gated mode active.")
        except asyncio.TimeoutError:
            if rag_bridge.visitor_state == "none":
                logger.info("No video track received after 3 seconds. Falling back to voice-only mode.")
                rag_bridge.visitor_state = "active"
                try:
                    await session.say(greeting, allow_interruptions=True)
                except Exception as e:
                    logger.warning("Failed to speak fallback greeting: %s", e)

    if bypass_vision:
        logger.info("BYPASS_VISION=True. Bypassing vision loop and activating voice directly.")
        rag_bridge.visitor_state = "active"
        async def say_immediate_greeting():
            try:
                await session.say(greeting, allow_interruptions=True)
            except Exception as e:
                logger.warning("Failed to speak immediate greeting: %s", e)
        asyncio.create_task(say_immediate_greeting())
    else:
        asyncio.create_task(check_video_timeout())

    # ---- Cleanup vision on disconnect ----
    @ctx.room.on("disconnected")
    def on_room_disconnected(*args, **kwargs):
        if vision is not None:
            vision.close()

    logger.info(
        "Agent ready — waiting for visitor to look at the robot before greeting."
    )

    # Keep the entrypoint alive until the room disconnects
    try:
        while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Agent job cancelled")
    finally:
        logger.info("Agent job session ended, cleaning up resources")
        if vision_task and not vision_task.done():
            vision_task.cancel()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_process,
            initialize_process_timeout=60.0,
            job_executor_type=JobExecutorType.PROCESS,
        )
    )
