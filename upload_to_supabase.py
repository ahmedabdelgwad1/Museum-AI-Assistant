"""
سكربت رفع بيانات المتحف إلى Supabase مع الـ Embeddings
يستخدم نفس موديل الـ Embeddings الموجود في الباك إند
"""

import csv
import json
import time
from sentence_transformers import SentenceTransformer
from supabase import create_client

# =============================================
# إعدادات Supabase
# =============================================
SUPABASE_URL = "https://fyeoccqyylbomsmwjwxh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZW9jY3F5eWxib21zbXdqd3hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEyOTA0NCwiZXhwIjoyMDk0NzA1MDQ0fQ.p9AbJJvOCuPTcsQXY-q50LqKgQsLW40QaNqchngplFM"

# نفس الموديل المستخدم في الباك إند (768 بُعد)
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
CSV_FILE = "bibalex_full_museum_data.csv"
TABLE_NAME = "museum_artifacts"
BATCH_SIZE = 10  # عدد الصفوف اللي بنرفعها دفعة واحدة

# =============================================
# الاتصال بـ Supabase
# =============================================
print("🔌 جاري الاتصال بـ Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ تم الاتصال بنجاح!")

# =============================================
# تحميل موديل الـ Embeddings
# =============================================
print(f"\n🤖 جاري تحميل موديل الـ Embeddings: {EMBEDDING_MODEL}")
print("(قد يستغرق دقيقتين في أول مرة فقط)")
model = SentenceTransformer(EMBEDDING_MODEL)
print("✅ تم تحميل الموديل!")

# =============================================
# قراءة ملف الـ CSV
# =============================================
print(f"\n📂 جاري قراءة ملف {CSV_FILE}...")
rows = []
with open(CSV_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"✅ تم قراءة {len(rows)} قطعة أثرية!")

# =============================================
# رفع البيانات دفعة دفعة
# =============================================
print(f"\n🚀 جاري رفع البيانات إلى Supabase ({TABLE_NAME})...")
success_count = 0
error_count = 0

for i in range(0, len(rows), BATCH_SIZE):
    batch = rows[i:i + BATCH_SIZE]
    records = []

    for row in batch:
        # النص الذي سيتم تحويله لـ Embedding (عربي + إنجليزي)
        text_to_embed = f"""
        Artifact: {row.get('Artifact Name English', '')}
        اسم القطعة: {row.get('Artifact Name Arabic', '')}
        Description: {row.get('Description English', '')[:500]}
        الوصف: {row.get('Description Arabic', '')[:500]}
        Hall: {row.get('Hall English', '')}
        القاعة: {row.get('Hall Arabic', '')}
        Category: {row.get('Category English', '')}
        التصنيف: {row.get('Category Arabic', '')}
        """.strip()

        # تحويل النص لـ Vector
        embedding = model.encode(text_to_embed).tolist()

        # البيانات الكاملة للقطعة
        metadata = {
            "section_number": row.get('Section Number', ''),
            "section_name_ar": row.get('Section Name Arabic', ''),
            "section_name_en": row.get('Section Name English', ''),
            "artifact_name_ar": row.get('Artifact Name Arabic', ''),
            "artifact_name_en": row.get('Artifact Name English', ''),
            "description_ar": row.get('Description Arabic', ''),
            "description_en": row.get('Description English', ''),
            "category_ar": row.get('Category Arabic', ''),
            "category_en": row.get('Category English', ''),
            "discovery_site_ar": row.get('Discovery site Arabic', ''),
            "discovery_site_en": row.get('Discovery Site English', ''),
            "hall_ar": row.get('Hall Arabic', ''),
            "hall_en": row.get('Hall English', ''),
            "link": row.get('Link', ''),
        }

        records.append({
            "content": text_to_embed,
            "metadata": json.dumps(metadata, ensure_ascii=False),
            "embedding": embedding
        })

    # رفع الدفعة لـ Supabase
    try:
        supabase.table(TABLE_NAME).insert(records).execute()
        success_count += len(batch)
        print(f"  ✅ [{i + len(batch)}/{len(rows)}] تم رفع {len(batch)} قطعة")
    except Exception as e:
        error_count += len(batch)
        print(f"  ❌ خطأ في الدفعة {i}: {e}")

    time.sleep(0.5)  # استراحة صغيرة لتجنب تجاوز حد الطلبات

# =============================================
# النتيجة النهائية
# =============================================
print(f"\n{'='*50}")
print(f"🎉 انتهى الرفع!")
print(f"  ✅ نجح: {success_count} قطعة")
print(f"  ❌ فشل: {error_count} قطعة")
print(f"{'='*50}")
