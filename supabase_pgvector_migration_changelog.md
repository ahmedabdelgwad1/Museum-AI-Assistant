# Supabase pgvector Migration Changelog

This file tracks the concrete project changes made during the Supabase/pgvector migration and frontend/admin sync work. Any future related change should be appended here with the date, changed files, and reason.

---

## 2026-05-20 — Remove Chroma Runtime and Use Supabase pgvector

### Summary

The project runtime was moved away from local ChromaDB and onto Supabase PostgreSQL with pgvector.

### Backend Changes

- Updated `backend/app/rag/vectorstore.py`
  - Uses Supabase client instead of ChromaDB.
  - Calls the configured RPC function, default: `match_artifacts`.
  - Reads/writes the configured table, default: `museum_artifacts`.
  - Added `add_documents()` to upsert `id`, `content`, `metadata`, and `embedding` into Supabase.
  - Added metadata filtering support for search filters.

- Updated `backend/main.py`
  - Health check now reports `supabase_pgvector`.
  - Startup logs Supabase pgvector status.
  - Removed legacy Chroma auto-indexing behavior from startup.

- Updated `backend/app/rag/retriever.py`
  - Removed Chroma-style filter syntax.
  - Uses simple metadata filter mapping compatible with the Supabase vectorstore wrapper.
  - Empty index warning now refers to Supabase artifact table.

- Updated `backend/scripts/index_artifacts.py`
  - Indexes CSV data into Supabase pgvector instead of ChromaDB.
  - Uses `add_documents()` from the Supabase vectorstore module.
  - Logs Supabase table and match function instead of Chroma collection/path.

- Updated `backend/scripts/test_rag.py`
  - CLI test output now says `Supabase pgvector`.

- Updated backend comments/docs in:
  - `backend/app/api/routes/artifacts.py`
  - `backend/app/api/routes/chat.py`
  - `backend/app/graph/nodes.py`
  - `backend/app/graph/state.py`
  - `backend/README.md`

- Added `backend/.dockerignore`
  - Excludes `.env`, virtualenvs, cache files, logs, audio files, and any generated Chroma folders.

- Removed local Chroma data folder:
  - `backend/data/chroma_db`

### Dependency State

- `backend/requirements.txt` does not include `chromadb`.
- Backend uses:
  - `supabase`
  - `sentence-transformers`
  - `fastapi`
  - `groq`
  - `langgraph`

### Verification

- Ran:

```bash
python3 -m compileall backend/app backend/main.py backend/scripts/index_artifacts.py backend/scripts/test_rag.py
```

- Result: passed.

---

## 2026-05-20 — Fix Admin Overview, Collection, and Acquisitions Supabase Flow

### Summary

Admin pages were already reading from Supabase, but errors were hidden. The Acquisitions page was inserting directly into Supabase from the frontend, which skipped embedding generation. This was fixed by routing creation through the backend.

### Frontend Changes

- Updated `forntent/src/app/admin/(dashboard)/page.tsx`
  - Overview reads from `museum_artifacts`.
  - Added console error logging for Supabase stats and recent artifact failures.

- Updated `forntent/src/app/admin/(dashboard)/artifacts/page.tsx`
  - Collection reads from `museum_artifacts`.
  - Added console error logging for count/list failures.
  - Keeps UI from silently showing empty results when Supabase returns an error.

- Updated `forntent/src/app/admin/(dashboard)/artifacts/new/page.tsx`
  - Acquisitions no longer inserts directly into Supabase from the browser.
  - Now calls backend `POST /artifacts`.
  - This ensures newly added artifacts receive embeddings and become searchable through pgvector.

- Updated `forntent/src/lib/api.ts`
  - Added `createArtifact()`.
  - Artifact reads now throw/log Supabase errors instead of silently returning empty data.
  - `createArtifact()` calls:

```http
POST {NEXT_PUBLIC_API_URL}/artifacts
```

### Backend Changes

- Updated `backend/app/models.py`
  - Added `ArtifactCreateRequest`.

- Updated `backend/app/api/routes/artifacts.py`
  - Added `POST /artifacts`.
  - Builds searchable artifact text.
  - Generates embedding with the backend embedding model.
  - Saves artifact into Supabase with `content`, `metadata`, and `embedding`.

### Why This Matters

Direct frontend inserts can save metadata, but they cannot safely generate and store embeddings because:

- The embedding model runs on the backend.
- The Supabase service role key must never be exposed in the frontend.
- pgvector search requires an embedding value.

So the correct flow is:

```text
Admin Acquisitions page
  -> Backend POST /artifacts
  -> Backend generates embedding
  -> Backend writes to Supabase museum_artifacts
  -> Artifact becomes visible and searchable
```

---

## 2026-05-20 — Fix Next.js Build Root Detection

### Summary

`npm run build` failed because Next.js/Turbopack inferred the wrong workspace root due to another lockfile above the frontend folder.

### Frontend Changes

- Updated `forntent/next.config.ts`
  - Added:

```ts
turbopack: {
  root: path.resolve(__dirname),
}
```

### Verification

- Ran:

```bash
npm run build
```

- Result: passed.

---

## 2026-05-20 — Cloud Deployment Notes

### Current Cloud Usage

The project already uses cloud for the data/vector layer:

```text
Supabase Cloud = PostgreSQL + pgvector + museum_artifacts
```

If running locally, the current setup is:

```text
Frontend local
Backend local
Database/vector store on Supabase Cloud
```

For full cloud deployment:

```text
Frontend on Vercel / Firebase Hosting / Azure Static Web Apps
Backend on Render / Railway / Google Cloud Run / Azure Container Apps
Database on Supabase Cloud
```

### Backend Environment Variables

```env
GROQ_API_KEY=your_groq_key
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_TABLE=museum_artifacts
SUPABASE_FUNCTION=match_artifacts
CORS_ORIGINS=["https://your-frontend-domain"]
```

### Frontend Environment Variables

```env
NEXT_PUBLIC_API_URL=https://your-backend-domain
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Important Security Rule

- Backend uses Supabase **service role key**.
- Frontend uses Supabase **anon key** only.
- Never expose the service role key in frontend code or `NEXT_PUBLIC_*` variables.

---

## Future Changes

Append future changes below this line.

---

## 2026-05-20 — Route Admin Reads Through Backend Service Role

### Problem

The admin dashboard still showed zero artifacts and a loading chart even though the project had moved to Supabase. The likely cause was that admin pages were reading directly from Supabase in the browser with the anon key. If Supabase RLS blocks anon `select`, the browser receives no usable data.

### Backend Changes

- Updated `backend/app/rag/vectorstore.py`
  - Added `list_records()` for raw admin records.
  - Added `delete_by_id()` for backend-powered deletes.
  - `list_records()` reads `id`, `content`, `metadata`, and `created_at` when available, with fallback to `id`, `content`, and `metadata`.

- Updated `backend/app/api/routes/artifacts.py`
  - Added `GET /artifacts/admin`.
  - Added `DELETE /artifacts/{artifact_id}`.
  - Admin listing and deletes now go through the backend Supabase service role key.

### Frontend Changes

- Updated `forntent/src/lib/api.ts`
  - Added `getAdminArtifacts()`.
  - Added `deleteArtifact()`.

- Updated `forntent/src/app/admin/(dashboard)/page.tsx`
  - Overview now loads stats, collection distribution, and recent activity from `GET /artifacts/admin`.

- Updated `forntent/src/app/admin/(dashboard)/artifacts/page.tsx`
  - Collection list now loads from `GET /artifacts/admin`.
  - Deletes now call backend `DELETE /artifacts/{artifact_id}`.

- Updated `forntent/src/app/admin/(dashboard)/artifacts/new/page.tsx`
  - Section dropdown now loads existing sections from `GET /artifacts/admin`.

### Resulting Admin Data Flow

```text
Admin UI
  -> NEXT_PUBLIC_API_URL
  -> Backend artifacts admin endpoints
  -> Supabase service role key
  -> museum_artifacts
```

This avoids browser-side RLS/anon-key read issues for admin pages.

### Verification

- Ran:

```bash
python3 -m compileall backend/app backend/main.py
npm run build
```

- Result: both passed.

---

## 2026-05-20 — Clean Chat and Voice API Contracts

### Summary

The chat and voice frontend calls were cleaned so they use environment-based backend URLs and match the FastAPI request contracts.

### Backend Changes

- Updated `backend/app/models.py`
  - `ChatRequest.conversation_history` now uses `Field(default_factory=list)`.
  - `ChatRequest.language` defaults to `"ar"`.
  - `ChatResponse.artifact_references` now uses `Field(default_factory=list)`.
  - This avoids mutable default list issues while preserving the existing response contract.

- Updated `backend/app/api/routes/voice.py`
  - Accepts optional `language` in the voice `FormData`.
  - Keeps transcript language detection as the primary signal.

### Frontend Changes

- Updated `forntent/src/hooks/useChat.ts`
  - Removed hardcoded Hugging Face backend URL.
  - Uses `NEXT_PUBLIC_API_URL` with local fallback `http://localhost:8000`.
  - `/chat` sends JSON with `query`, `language`, and `conversation_history`.
  - `/voice` sends `FormData` with `file`, `language`, and `conversation_history`.
  - Does not set `Content-Type` manually for `FormData`.

- Updated `forntent/src/lib/api.ts`
  - Removed unused `artifact_context` payload from `sendChatMessage()`.
  - `sendChatMessage()` now accepts `query`, `history`, and `locale`.
  - `sendVoiceMessage()` now uses the FastAPI field name `file` instead of `audio`.
  - `sendVoiceMessage()` now returns the backend JSON response instead of assuming a raw blob.

- Updated `forntent/src/lib/ai/chat.ts`
  - Removed hardcoded Hugging Face backend URL.
  - Added optional `conversation_history` support.

### Verification

- Confirmed no remaining frontend references to:
  - `ahmed3182004-museum-backend`
  - `artifact_context`
  - `formData.append("audio", ...)`

- Ran:

```bash
python3 -m compileall backend/app backend/main.py
npm run build
```

- Result: both passed.
