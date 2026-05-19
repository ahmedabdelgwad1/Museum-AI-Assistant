import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv("backend/.env")
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# Simulate what the generate_answer node does
try:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "أنت روبوت مرشد سياحي في المتحف."},
            {"role": "user", "content": "ازيك؟"}
        ],
        max_tokens=1200,
        temperature=0.4
    )
    print("SUCCESS:", completion.choices[0].message.content)
except Exception as e:
    print("ERROR:", type(e).__name__, str(e))
