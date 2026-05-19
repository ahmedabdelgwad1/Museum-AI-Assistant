import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv("backend/.env")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("GROQ_API_KEY not found in .env")
    exit(1)

client = Groq(api_key=api_key)

try:
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=10
    )
    print("Success! Response:", completion.choices[0].message.content)
except Exception as e:
    print("Error:", e)
