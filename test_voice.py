import requests
import os

# Create a small valid WAV file (sine wave)
import wave, struct, math
sample_rate = 16000
duration = 1.0
wavef = wave.open('valid.wav', 'w')
wavef.setnchannels(1)
wavef.setsampwidth(2)
wavef.setframerate(sample_rate)
for i in range(int(sample_rate * duration)):
    value = int(32767.0 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
    wavef.writeframesraw(struct.pack('<h', value))
wavef.close()

url = "https://ahmed3182004-museum-backend.hf.space/voice"
with open('valid.wav', 'rb') as f:
    files = {'file': ('valid.wav', f, 'audio/wav')}
    response = requests.post(url, files=files)

print("Status Code:", response.status_code)
try:
    print("Headers X-Transcript:", response.headers.get("X-Transcript"))
except:
    pass
print("Response text:", response.text[:500])
