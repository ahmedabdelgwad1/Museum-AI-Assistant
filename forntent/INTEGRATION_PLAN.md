# 🏛️ خطة ربط الـ UI بالـ AI Backend — متحف مكتبة الإسكندرية

> **التاريخ:** مايو 2026  
> **الهدف:** ربط الـ Next.js Frontend بالـ FastAPI AI Backend مع Supabase كقاعدة بيانات، والتخطيط للانتقال من Chroma إلى pgvector (PyVector).

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Next.js Frontend (UI)                  │
│   /[locale]/*  ·  /admin/(dashboard)/*  ·  Components   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI AI Backend                         │
│   /chat  ·  /voice  ·  /artifacts  ·  /search          │
└────────────┬────────────────────┬───────────────────────┘
             │                    │
             ▼                    ▼
┌──────────────────┐   ┌──────────────────────────────────┐
│    Supabase       │   │  Vector Store                    │
│  (PostgreSQL)     │   │  [CURRENT]  Chroma               │
│  - artifacts      │   │  [FUTURE]   pgvector (Supabase)  │
│  - sections       │   │  → سيتم الدمج في Supabase نفسها  │
│  - users/admins   │   └──────────────────────────────────┘
└──────────────────┘
```

---

## 1️⃣ إعداد طبقة API في الـ Frontend

### أنشئ ملف: `src/lib/api.ts`

```typescript
// src/lib/api.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  // ── Chat ──────────────────────────────────────────────────────────
  async chat(message: string, sessionId: string, locale: "en" | "ar") {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId, locale }),
    });
    return res.json(); // { answer: string, sources: ArtifactRef[] }
  },

  // ── Voice (Whisper STT) ────────────────────────────────────────────
  async transcribeVoice(audioBlob: Blob, locale: "en" | "ar") {
    const form = new FormData();
    form.append("file", audioBlob, "audio.webm");
    form.append("locale", locale);
    const res = await fetch(`${BASE_URL}/voice/transcribe`, {
      method: "POST",
      body: form,
    });
    return res.json(); // { transcript: string }
  },

  // ── Artifacts (CRUD via FastAPI → Supabase) ───────────────────────
  async getArtifacts(page = 1, limit = 20, sectionId?: string) {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (sectionId) params.append("section_id", sectionId);
    const res = await fetch(`${BASE_URL}/artifacts?${params}`);
    return res.json(); // { data: Artifact[], total: number }
  },

  async getArtifact(id: string) {
    const res = await fetch(`${BASE_URL}/artifacts/${id}`);
    return res.json(); // Artifact
  },

  async createArtifact(payload: FormData, token: string) {
    const res = await fetch(`${BASE_URL}/artifacts`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: payload,
    });
    return res.json();
  },

  async updateArtifact(id: string, payload: Partial<Artifact>, token: string) {
    const res = await fetch(`${BASE_URL}/artifacts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  async deleteArtifact(id: string, token: string) {
    await fetch(`${BASE_URL}/artifacts/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // ── Sections ──────────────────────────────────────────────────────
  async getSections() {
    const res = await fetch(`${BASE_URL}/sections`);
    return res.json(); // Section[]
  },

  // ── Semantic Search (RAG) ─────────────────────────────────────────
  async semanticSearch(query: string, locale: "en" | "ar", topK = 5) {
    const res = await fetch(`${BASE_URL}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, locale, top_k: topK }),
    });
    return res.json(); // { results: ArtifactRef[] }
  },
};

// Types
export interface Artifact {
  id: string;
  name_en: string;
  name_ar: string;
  description_en: string;
  description_ar: string;
  section_id: string;
  image_url: string;
  period: string;
  created_at: string;
}

export interface ArtifactRef {
  id: string;
  name_en: string;
  name_ar: string;
  score: number;
}

export interface Section {
  id: string;
  name_en: string;
  name_ar: string;
  slug: string;
}
```

---

## 2️⃣ متغيرات البيئة المطلوبة

```bash
# .env.local  (Frontend)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

```bash
# .env  (FastAPI Backend)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...          # أو مفتاح Groq للـ Whisper
CHROMA_HOST=localhost           # حاليًا
CHROMA_PORT=8001
# ─── مستقبلًا بعد الانتقال ───
# PGVECTOR_CONN=postgresql://...supabase.co/postgres
```

---

## 3️⃣ ربط كل صفحة بالـ Backend

### 🔵 صفحة القطع الأثرية العامة — `/[locale]/artifacts/[artifactId]`

**الآن:** بيانات ستاتيكية  
**المطلوب:**
```typescript
// src/app/[locale]/artifacts/[artifactId]/page.tsx
import { api } from "@/lib/api";

export default async function ArtifactDetailPage({ params }) {
  const artifact = await api.getArtifact(params.artifactId);
  // عرض artifact.name_ar / artifact.name_en حسب params.locale
}
```
- ✅ يُعرض: الاسم، الوصف، الصورة، القسم، الحقبة الزمنية
- ✅ يُفعَّل: زر "اسألني عن هذه القطعة" → يفتح FloatingAIButton مع context القطعة

---

### 🔵 صفحة الأقسام — `/[locale]/sections/[sectionId]`

**المطلوب:**
```typescript
// src/app/[locale]/sections/[sectionId]/page.tsx
import { api } from "@/lib/api";

export default async function SectionPage({ params }) {
  const artifacts = await api.getArtifacts(1, 20, params.sectionId);
  // عرض grid الـ artifacts مع Pagination
}
```

---

### 🟡 FloatingAIButton — الذكاء الاصطناعي للزوار

**الملف:** `src/components/layout/FloatingAIButton.tsx`

**التعديلات المطلوبة على دالة `send`:**
```typescript
// استبدال الـ setTimeout المؤقت بـ:
const send = async (msg: string) => {
  if (!msg.trim()) return;
  setMessages(p => [...p, { role: "user", content: msg }]);
  setInput("");
  setIsLoading(true);

  const { answer, sources } = await api.chat(msg, sessionId, locale);

  setMessages(p => [...p, {
    role: "ai",
    content: answer,
    sources,          // روابط على القطع المرتبطة بالإجابة
  }]);
  setIsLoading(false);
};
```

**التعديلات المطلوبة على `startRecording` → `onstop`:**
```typescript
mediaRecorder.onstop = async () => {
  const audioBlob = new Blob(chunks, { type: "audio/webm" });

  // 1. إرسال الصوت لـ Whisper عبر FastAPI
  const { transcript } = await api.transcribeVoice(audioBlob, locale);

  // 2. عرض ما قاله المستخدم
  setMessages(p => [...p, { role: "user", content: transcript }]);

  // 3. إرسال النص للـ RAG
  const { answer } = await api.chat(transcript, sessionId, locale);
  setMessages(p => [...p, { role: "ai", content: answer }]);
};
```

---

### 🔴 لوحة الأدمن — `/admin/(dashboard)/artifacts`

**الآن:** بيانات hardcoded (4 قطع وهمية)  
**المطلوب:**

```typescript
// src/app/admin/(dashboard)/artifacts/page.tsx
"use client";
import { useEffect, useState } from "react";
import { api, Artifact } from "@/lib/api";
import { useAdminAuth } from "@/context/AdminAuthContext"; // سيُنشأ

export default function AdminArtifacts() {
  const { token } = useAdminAuth();
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [total, setTotal]         = useState(0);
  const [page, setPage]           = useState(1);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    api.getArtifacts(page, 20).then(({ data, total }) => {
      setArtifacts(data);
      setTotal(total);
      setLoading(false);
    });
  }, [page]);

  const handleDelete = async (id: string) => {
    await api.deleteArtifact(id, token);
    setArtifacts(p => p.filter(a => a.id !== id));
  };

  // ... باقي الـ JSX كما هو لكن على artifacts الحقيقية
}
```

---

### 🔴 صفحة إضافة قطعة جديدة — `/admin/(dashboard)/artifacts/new`

```typescript
// src/app/admin/(dashboard)/artifacts/new/page.tsx
const handleSubmit = async (e: FormEvent) => {
  e.preventDefault();
  const form = new FormData();
  form.append("name_en",         nameEn);
  form.append("name_ar",         nameAr);
  form.append("description_en",  descEn);
  form.append("description_ar",  descAr);
  form.append("section_id",      sectionId);
  form.append("period",          period);
  form.append("image",           imageFile);   // الصورة مباشرة

  await api.createArtifact(form, token);
  router.push("/admin/artifacts");
};
```
> **ملاحظة:** الـ FastAPI ترفع الصورة إلى Supabase Storage وترجع الـ `image_url` وتحفظها في `artifacts` table.

---

### 🔴 الـ Settings Page — `/admin/(dashboard)/settings`

```typescript
// إضافة قسم "Vector DB Settings" لاحقًا
// - عرض إحصائيات الـ vector store (عدد الـ embeddings)
// - زر "Re-index All Artifacts" → POST /admin/reindex
// - مؤشر الانتقال من Chroma إلى pgvector
```

---

## 4️⃣ Supabase Schema المطلوب

```sql
-- artifacts table
create table artifacts (
  id            uuid primary key default gen_random_uuid(),
  name_en       text not null,
  name_ar       text not null,
  description_en text,
  description_ar text,
  section_id    uuid references sections(id),
  image_url     text,
  period        text,
  created_at    timestamptz default now()
);

-- sections table
create table sections (
  id       uuid primary key default gen_random_uuid(),
  name_en  text not null,
  name_ar  text not null,
  slug     text unique not null
);

-- chat_sessions table (اختياري - لحفظ المحادثات)
create table chat_sessions (
  id         uuid primary key default gen_random_uuid(),
  session_id text not null,
  role       text check (role in ('user','ai')),
  content    text,
  locale     text,
  created_at timestamptz default now()
);
```

---

## 5️⃣ 🔄 الانتقال من Chroma إلى pgvector (PyVector)

### الوضع الحالي
```
artifacts data → index_artifacts.py → Chroma (local) → FastAPI /search
```

### الوضع المستهدف
```
artifacts data → index_artifacts.py → pgvector (Supabase) → FastAPI /search
                                       ↑
                              نفس قاعدة البيانات!
                              لا server منفصل
```

### خطوات الانتقال

#### الخطوة 1 — تفعيل pgvector في Supabase
```sql
-- في Supabase SQL Editor:
create extension if not exists vector;

-- إضافة عمود الـ embedding لجدول artifacts
alter table artifacts add column embedding vector(1536);

-- إنشاء index للبحث السريع
create index on artifacts using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
```

#### الخطوة 2 — تعديل `index_artifacts.py` في الـ Backend
```python
# index_artifacts.py  (BEFORE - Chroma)
import chromadb
client = chromadb.Client()
collection = client.get_or_create_collection("museum")
collection.add(documents=texts, embeddings=embeddings, ids=ids)

# index_artifacts.py  (AFTER - pgvector via Supabase)
from supabase import create_client
import openai  # أو Groq لـ embeddings

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

for artifact in artifacts:
    text = f"{artifact['name_en']} {artifact['description_en']}"
    embedding = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    ).data[0].embedding

    supabase.table("artifacts").update({
        "embedding": embedding
    }).eq("id", artifact["id"]).execute()
```

#### الخطوة 3 — تعديل `/search` endpoint في FastAPI
```python
# BEFORE (Chroma):
results = collection.query(query_embeddings=[q_embedding], n_results=5)

# AFTER (pgvector via Supabase RPC):
results = supabase.rpc("match_artifacts", {
    "query_embedding": q_embedding,
    "match_threshold": 0.7,
    "match_count": 5
}).execute()
```

#### الخطوة 4 — إنشاء Supabase Function للبحث
```sql
-- دالة البحث في Supabase
create or replace function match_artifacts(
  query_embedding vector(1536),
  match_threshold float,
  match_count     int
)
returns table (
  id          uuid,
  name_en     text,
  name_ar     text,
  description_en text,
  similarity  float
)
language sql stable
as $$
  select
    id, name_en, name_ar, description_en,
    1 - (embedding <=> query_embedding) as similarity
  from artifacts
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
```

### مقارنة Chroma vs pgvector

| الجانب | Chroma (حاليًا) | pgvector / Supabase (مستقبلًا) |
|--------|----------------|-------------------------------|
| الاستضافة | Local / منفصل | Supabase (نفس DB) |
| الصيانة | يحتاج server منفصل | لا يحتاج |
| الـ Persistence | ملفات محلية | Cloud PostgreSQL |
| الدمج مع البيانات | صعب (IDs فقط) | سهل (JOIN مباشر) |
| الأمان | لا auth | Supabase RLS |
| التكلفة | مجاني local | Free tier كافي |

---

## 6️⃣ أولوية التنفيذ (Roadmap)

```
Phase 1 — الربط الأساسي (الأهم الآن)
├── [ ] إنشاء src/lib/api.ts
├── [ ] إنشاء src/lib/supabaseClient.ts
├── [ ] تعديل FloatingAIButton → chat حقيقي
└── [ ] تعديل FloatingAIButton → voice حقيقي (Whisper)

Phase 2 — بيانات حقيقية في الـ UI
├── [ ] ربط /[locale]/artifacts/[artifactId] بـ Supabase
├── [ ] ربط /[locale]/sections/[sectionId] بـ Supabase
├── [ ] ربط Admin Artifacts page بـ API (بدل hardcoded)
└── [ ] Admin Auth (Supabase Auth أو JWT)

Phase 3 — إضافة / تعديل / حذف قطعة
├── [ ] Admin New Artifact Form → POST /artifacts
├── [ ] Admin Edit Artifact → PATCH /artifacts/:id
└── [ ] Supabase Storage لرفع الصور

Phase 4 — الانتقال إلى pgvector
├── [ ] تفعيل pgvector extension في Supabase
├── [ ] إضافة عمود embedding لجدول artifacts
├── [ ] تعديل index_artifacts.py
├── [ ] تعديل /search endpoint في FastAPI
└── [ ] اختبار جودة البحث مقارنةً بـ Chroma

Phase 5 — Polish
├── [ ] حفظ المحادثات في chat_sessions table
├── [ ] Admin Settings → إحصائيات ومؤشرات RAG
└── [ ] Error handling + Loading states في كل الصفحات
```

---

## 7️⃣ ملاحظات مهمة

> **CORS:** يجب إضافة `allow_origins=["http://localhost:3000", "https://domain.com"]` في FastAPI.

> **Session ID:** يُنشأ في الـ Frontend عند أول رسالة ويُحفظ في `localStorage` أو `sessionStorage` حتى يتذكر الـ AI سياق المحادثة.

> **Image Upload:** الصور ترفع إلى Supabase Storage bucket اسمه `artifact-images`، والـ FastAPI يرجع الـ public URL بعد الرفع.

> **RLS (Row Level Security):** يجب تفعيله في Supabase بحيث:
> - القراءة `public` مفتوحة للجميع
> - الكتابة/الحذف محصورة بـ `admin` role فقط
