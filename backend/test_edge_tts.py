from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS

import asyncio
import edge_tts
import uuid
from livekit.agents import tts

class EdgeTTS(tts.TTS):
    def __init__(self, voice="ar-EG-SalmaNeural"):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self._voice = voice

    def synthesize(self, text: str, **kwargs) -> tts.ChunkedStream:
        return _EdgeChunkedStream(tts=self, input_text=text, conn_options=kwargs.get("conn_options", DEFAULT_API_CONNECT_OPTIONS))

class _EdgeChunkedStream(tts.ChunkedStream):
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        output_emitter.initialize(
            request_id=uuid.uuid4().hex,
            sample_rate=self._tts.sample_rate,
            num_channels=self._tts.num_channels,
            mime_type="mp3"
        )

        communicate = edge_tts.Communicate(self._input_text, self._tts._voice)
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                output_emitter.push(chunk["data"])
                

async def main():
    my_tts = EdgeTTS()
    stream = my_tts.synthesize("مرحبا بك")
    async for chunk in stream:
        print(f"Got chunk: {chunk.frame.samples_per_channel} samples")

if __name__ == "__main__":
    asyncio.run(main())
