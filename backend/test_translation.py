import asyncio
from app.api.routes.artifacts import TranslateRequest, translate_text

async def main():
    req = TranslateRequest(text="لوحة ألوان الملك نعرمر", target_lang="en")
    print("Sending request...")
    res = await translate_text(req)
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
