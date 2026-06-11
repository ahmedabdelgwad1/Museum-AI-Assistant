import edge_tts
import uuid
from livekit.agents import tts
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS

class EdgeTTS(tts.TTS):
    """
    Custom LiveKit TTS Plugin that uses Microsoft Edge TTS.
    Outputs Arabic voices perfectly for free.
    """
    def __init__(self, voice="ar-EG-SalmaNeural", **kwargs):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
            **kwargs
        )
        self._voice = voice

    def synthesize(self, text: str, **kwargs) -> tts.ChunkedStream:
        return _EdgeChunkedStream(
            tts=self, 
            input_text=text, 
            conn_options=kwargs.get("conn_options", DEFAULT_API_CONNECT_OPTIONS)
        )

class _EdgeChunkedStream(tts.ChunkedStream):
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        output_emitter.initialize(
            request_id=uuid.uuid4().hex,
            sample_rate=self._tts.sample_rate,
            num_channels=self._tts.num_channels,
            mime_type="mp3"
        )

        communicate = edge_tts.Communicate(self._input_text, self._tts._voice, rate="+10%")
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                output_emitter.push(chunk["data"])
