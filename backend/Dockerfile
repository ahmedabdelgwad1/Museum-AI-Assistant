FROM python:3.10

# مسار العمل
WORKDIR /app

# مجلد بيانات قابل للكتابة (مطلوب لـ Hugging Face)
RUN mkdir -p /app/data && chmod 777 /app/data

# تثبيت حزم النظام المطلوبة لـ OpenCV و Mediapipe
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 libgles2 libegl1 wget && rm -rf /var/lib/apt/lists/*

# تثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود المشروع
COPY . .

# تحميل ملف الذكاء الاصطناعي للكاميرا
RUN wget -qO /app/app/face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task

# صلاحيات الكتابة
RUN chmod -R 777 /app && chmod +x /app/start.sh

# البورت الخاص بـ Hugging Face
EXPOSE 7860

# تشغيل FastAPI + LiveKit Agent معاً
CMD ["/bin/bash", "/app/start.sh"]
