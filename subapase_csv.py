from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import HuggingFaceEmbeddings # أو أي موديل بتستخدمه
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client
import os

# بيانات الاتصال بـ Supabase
supabase_url = "https://fyeoccqyylbomsmwjwxh.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZW9jY3F5eWxib21zbXdqd3hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEyOTA0NCwiZXhwIjoyMDk0NzA1MDQ0fQ.p9AbJJvOCuPTcsQXY-q50LqKgQsLW40QaNqchngplFM" # استخدم الـ Service Role عشان تقدر تكتب في الـ DB
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