import asyncio
import os
import sys

# Append backend path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.edge_tts_plugin import EdgeTTS
from livekit.agents.tts import AudioEmitter, ChunkedStream

async def main():
    try:
        tts = EdgeTTS()
        print("EdgeTTS initialized")
        stream = tts.synthesize("اهلا بك")
        print("Stream created")
        
        class MockEmitter:
            def initialize(self, *args, **kwargs):
                print("Emitter initialized with", args, kwargs)
            def push(self, data):
                print("Emitter pushed data length:", len(data))
        
        # Test if edge_tts can stream properly
        import edge_tts
        comm = edge_tts.Communicate("اهلا", "ar-EG-SalmaNeural")
        count = 0
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                count += 1
        print("EdgeTTS successfully returned", count, "audio chunks")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
