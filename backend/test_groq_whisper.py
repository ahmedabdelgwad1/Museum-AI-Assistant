import os
from groq import Groq
client = Groq()
print(client.audio.transcriptions.create.__doc__)
