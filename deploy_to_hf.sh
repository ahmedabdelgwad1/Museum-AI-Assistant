#!/bin/bash
# deploy_to_hf.sh
# سكريبت لرفع الباك إند فقط على Hugging Face Space جديدة
# الاستخدام: bash deploy_to_hf.sh <HF_TOKEN> <HF_SPACE_ID>
# مثال: bash deploy_to_hf.sh hf_xxxx Ahmed3182004/museum-backend-api

set -e

HF_TOKEN=$1
HF_SPACE_ID=$2

if [ -z "$HF_TOKEN" ] || [ -z "$HF_SPACE_ID" ]; then
  echo "❌ الاستخدام: bash deploy_to_hf.sh <HF_TOKEN> <HF_SPACE_ID>"
  echo "   مثال: bash deploy_to_hf.sh hf_xxxx Ahmed3182004/museum-backend-api"
  exit 1
fi

echo "🚀 جاري تجهيز نسخة نظيفة من الباك إند..."

# إنشاء مجلد مؤقت
DEPLOY_DIR=$(mktemp -d)
echo "📁 مجلد النشر المؤقت: $DEPLOY_DIR"

# نسخ ملفات الباك إند فقط (بدون binary)
cp -r backend/app "$DEPLOY_DIR/"
cp backend/main.py "$DEPLOY_DIR/"
cp backend/requirements.txt "$DEPLOY_DIR/"
cp backend/Dockerfile "$DEPLOY_DIR/"
cp backend/.env.example "$DEPLOY_DIR/" 2>/dev/null || true

# إنشاء README.md مع إعدادات Hugging Face
cat > "$DEPLOY_DIR/README.md" << 'EOF'
---
title: Museum Backend API
emoji: 🏛️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Museum AI Assistant Backend

FastAPI + LangGraph Corrective RAG backend for the Bibliotheca Alexandrina Antiquities Museum.

## Features
- 🔄 Corrective RAG pipeline (LangGraph)
- 🌐 Arabic & English support
- ⚡ FastAPI with full OpenAPI docs
EOF

# إنشاء .gitignore للمجلد المؤقت
cat > "$DEPLOY_DIR/.gitignore" << 'EOF'
__pycache__/
*.pyc
*.pyo
.env
session_logs/
*.log
*.pt
*.task
*.npy
*.png
*.jpg
*.jpeg
*.pdf
*.csv
EOF

echo "✅ الملفات المنسوخة:"
ls -la "$DEPLOY_DIR/"

# تهيئة git ورفع على HF
cd "$DEPLOY_DIR"
git init
git checkout -b main
git config user.email "deploy@museum-ai.com"
git config user.name "Museum Deploy"

git add .
git commit -m "Deploy backend to Hugging Face Space"

echo ""
echo "📤 جاري الرفع على Hugging Face Space: $HF_SPACE_ID"
git push -f https://user:${HF_TOKEN}@huggingface.co/spaces/${HF_SPACE_ID} main

echo ""
echo "✅ تم الرفع بنجاح!"
echo "🔗 الرابط: https://huggingface.co/spaces/$HF_SPACE_ID"

# تنظيف المجلد المؤقت
cd -
rm -rf "$DEPLOY_DIR"
echo "🧹 تم تنظيف المجلد المؤقت"
