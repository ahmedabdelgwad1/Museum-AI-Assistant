import os
import json
from dotenv import load_dotenv
from supabase import create_client

# 1. تحميل الإعدادات من ملف .env
load_dotenv("backend/.env")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ تأكد من وجود SUPABASE_URL و SUPABASE_KEY في ملف backend/.env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "artifact-images"  # تأكد إن ده اسم الـ bucket الصح عندك
TABLE_NAME = "museum_artifacts"

print("🔗 جاري الاتصال بقاعدة البيانات و Storage...")

def get_best_image(file_list):
    """تختار أفضل صورة من القائمة المتاحة"""
    if not file_list:
        return None
    for f in file_list:
        name = f['name'].lower()
        if "main" in name or "1" in name:
            return f['name']
    # استبعاد ملفات النظام المخفية لو موجودة
    valid_files = [f['name'] for f in file_list if f['name'] != '.emptyFolderPlaceholder' and not f['name'].startswith('.')]
    return valid_files[0] if valid_files else None

def link_images():
    # 2. جلب كل القطع الأثرية من الداتا بيز
    print("📦 جاري جلب القطع الأثرية من الداتا بيز...")
    response = supabase.table(TABLE_NAME).select("id, metadata").execute()
    artifacts = response.data
    
    if not artifacts:
        print("⚠️ لم يتم العثور على قطع أثرية في الجدول!")
        return

    success_count = 0
    fail_count = 0

    for item in artifacts:
        artifact_id = item['id']
        meta = item.get('metadata', {})
        
        # التأكد من أن الميتاداتا عبارة عن Dictionary
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except:
                meta = {}

        hall_en = meta.get("hall_en")
        artifact_name_en = meta.get("artifact_name_en")

        if not hall_en or not artifact_name_en:
            continue
            
        # تنظيف اسم القاعة ليتطابق مع الـ Storage (إزالة كلمة showcase وما بعدها)
        clean_hall = hall_en.split(", showcase")[0].strip()
        
        # بعض التعديلات لأسماء القاعات لتتطابق مع الـ Bucket
        if "Antiquities of the BA Site" in clean_hall:
            clean_hall = "Antiquities of Bibliotheca Alexandrina"
        if "Nelson Island Collection" in clean_hall:
            clean_hall = "Nelson Island"

        # 3. البحث في الـ Storage عن هذا المسار: Hall / Artifact
        folder_path = f"{clean_hall}/{artifact_name_en}"
        try:
            # list files in that specific folder in Supabase Storage
            files_response = supabase.storage.from_(BUCKET_NAME).list(folder_path)
            
            if files_response:
                best_image = get_best_image(files_response)
                
                if best_image:
                    # 4. بناء الرابط العام (Public URL)
                    # نعمل URL Encoding للمسافات
                    from urllib.parse import quote
                    safe_path = quote(f"{folder_path}/{best_image}")
                    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{safe_path}"
                    
                    # 5. تحديث الـ Metadata في قاعدة البيانات وإضافة رابط الصورة
                    meta["image_url"] = public_url
                    
                    # الرفع لـ Supabase
                    supabase.table(TABLE_NAME).update({"metadata": meta}).eq("id", artifact_id).execute()
                    
                    print(f"✅ تم الربط: {artifact_name_en}")
                    success_count += 1
                else:
                    print(f"⚠️ الفولدر موجود لكن فارغ: {folder_path}")
                    fail_count += 1
            else:
                print(f"⚠️ لم يتم العثور على فولدر في الـ Storage: {folder_path}")
                fail_count += 1
                
        except Exception as e:
            print(f"❌ خطأ أثناء معالجة القطعة '{artifact_name_en}': {e}")
            fail_count += 1

    print("\n" + "="*40)
    print(f"🎉 تمت العملية بنجاح!")
    print(f"✅ تم ربط: {success_count} صورة")
    print(f"❌ لم يتم العثور على صور لـ: {fail_count} قطعة")
    print("="*40)

if __name__ == "__main__":
    link_images()
