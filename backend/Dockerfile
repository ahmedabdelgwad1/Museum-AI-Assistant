FROM python:3.10

# إنشاء مسار العمل داخل الحاوية
WORKDIR /app

# إنشاء مجلد للبيانات بصلاحيات تسمح بالكتابة (مهم جداً لـ Hugging Face)
RUN mkdir -p /app/data && chmod 777 /app/data

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# إعطاء صلاحيات القراءة والكتابة لكل الملفات للمستخدم الخاص بـ Hugging Face
RUN chmod -R 777 /app

# منصة Hugging Face تستخدم البورت 7860 بشكل افتراضي
EXPOSE 7860

# تشغيل السيرفر
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
