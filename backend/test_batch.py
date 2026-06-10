import asyncio
from app.api.routes.artifacts import BatchTranslateRequest, translate_batch
from app.models import BatchTranslateField

async def main():
    req = BatchTranslateRequest(fields_to_translate=[
        BatchTranslateField(field_id="name_ar", source_text="Palette of King Narmer", target_lang="ar"),
        BatchTranslateField(field_id="desc_en", source_text="لوحة تاريخية", target_lang="en")
    ])
    print("Sending batch request...")
    res = await translate_batch(req)
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
