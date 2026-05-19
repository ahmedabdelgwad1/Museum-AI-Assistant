from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import HuggingFaceEmbeddings # أو أي موديل بتستخدمه
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client
import os

# بيانات الاتصال بـ Supabase
supabase_url = os.environ.get("SUPABASE_URL", "https://fyeoccqyylbomsmwjwxh.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY", "") # استخدم الـ Service Role عشان تقدر تكتب في الـ DB

if not supabase_key:
    supabase_key = input("🔑 الرجاء إدخال Supabase Service Role Key: ").strip()

supabase: Client = create_client(supabase_url, supabase_key)

# 1. قراءة الـ CSV
loader = CSVLoader(file_path="bibalex_full_museum_data.csv", encoding="utf-8")
documents = loader.load()

# 2. تحديد موديل الـ Embeddings
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base") # ممتاز للعربي والإنجليزي

# 3. رفع الداتا والـ Embeddings لـ Supabase
vector_store = SupabaseVectorStore.from_documents(
    documents,
    embeddings,
    client=supabase,
    table_name="museum_artifacts",
    query_name="match_artifacts"
)
print("تم رفع بيانات المتحف بنجاح!")