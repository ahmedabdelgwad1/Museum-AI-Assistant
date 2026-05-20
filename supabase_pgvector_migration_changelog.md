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

---

## 2026-05-20 — Add Admin Supabase Fallback When Backend Is Offline

### Problem

The public language/sections pages could show sections because they read directly from Supabase in the browser. Admin pages were routed through `NEXT_PUBLIC_API_URL` and stayed empty when the local backend at `http://127.0.0.1:8000` was not running.

### Frontend Changes

- Updated `forntent/src/lib/api.ts`
  - `getAdminArtifacts()` now tries `GET /artifacts/admin` first.
  - If the backend is unavailable or returns an error, it falls back to reading `museum_artifacts` directly through the Supabase browser client.
  - This lets Admin Overview, Collection, and the Acquisitions section dropdown show data during local frontend-only development.
  - Artifact creation still uses the backend because embeddings must be generated server-side.

### Important Note

For full admin functionality, especially creating searchable artifacts and deleting records, the FastAPI backend still needs to be running because those actions require the Supabase service role key and/or embedding generation.

### Verification

- Confirmed local backend was not reachable at `http://127.0.0.1:8000/health`.
- Ran:

```bash
npm run build
python3 -m compileall backend/app backend/main.py
```

- Result: both passed.

---

## 2026-05-20 — Adopt Hybrid Admin Architecture

### Decision

Admin read operations now use Supabase directly from the Next.js frontend with the public anon key. Admin write/delete operations stay routed through FastAPI.

### Final Admin Flow

```text
Admin Overview / Collection / section dropdown
  -> Next.js
  -> Supabase direct SELECT

Admin Create Artifact
  -> Next.js
  -> FastAPI POST /artifacts
  -> embedding generation
  -> Supabase upsert

Admin Delete Artifact
  -> Next.js
  -> FastAPI DELETE /artifacts/{artifact_id}
  -> Supabase delete with service role key
```

### Frontend Changes

- Updated `forntent/src/lib/api.ts`
  - `getAdminArtifacts()` now reads directly from Supabase.
  - Removed the backend-first admin read attempt and fallback branch.
  - Selects `id`, `content`, and `metadata` from `museum_artifacts`.

### Security Model

- Supabase anon key is used only for read/list operations.
- Supabase RLS should allow `SELECT` on public artifact data.
- Supabase RLS should block anon `INSERT`, `UPDATE`, and `DELETE`.
- FastAPI remains responsible for privileged write/delete actions and embedding generation.

### Verification

- Ran:

```bash
npm run build
python3 -m compileall backend/app backend/main.py
```

- Result: both passed.

---

## 2026-05-20 — Fix Next.js 16 Build Warnings (Turbopack Root & Middleware→Proxy)

### Summary

تم إصلاح تحذيرَين (Warnings) كانا يظهران في الـ Build Output بدون أن يوقفا الـ Deployment، وذلك للحفاظ على Clean Build Console ومنع أي مشاكل مستقبلية مع تحديثات Next.js.

### Root Cause Analysis

**تحذير ١ — Workspace Root Ambiguity:**
Next.js اكتشف أكثر من ملف `package-lock.json` على الجهاز (`/Users/apple/package-lock.json` و `forntent/package-lock.json`)، فاختار الغلط وأصدر تحذير إن الـ workspace root مش محدد بشكل صحيح.

**تحذير ٢ — Deprecated Middleware Convention:**
Next.js 16 غيّر الـ convention الخاص بالـ middleware؛ بقى اسم الملف والدالة المعيارية هو `proxy` بدل `middleware`.

### Frontend Changes

- Updated `forntent/next.config.ts`
  - Added explicit `turbopack.root` pointing to `path.resolve(__dirname)` (the `forntent` directory).
  - Silences the "workspace root inferred incorrectly" warning caused by multiple `package-lock.json` files detected in parent directories.

- Renamed `forntent/src/middleware.ts` → `forntent/src/proxy.ts`
  - Follows the new Next.js 16 file convention: `proxy.ts` instead of `middleware.ts`.
  - Renamed the exported function from `middleware` to `proxy` as required by the new convention.
  - All logic inside the function (`updateSession` for Supabase auth) remains unchanged.

### Files Changed

| File | Action |
|------|--------|
| `forntent/next.config.ts` | Modified — added `turbopack.root` |
| `forntent/src/middleware.ts` | Deleted |
| `forntent/src/proxy.ts` | Created (renamed + function export updated) |

### Verification

- Ran:

```bash
npm run build
```

- Result: passed with zero warnings. Console output shows `✓ Compiled successfully` and `ƒ Proxy (Middleware)` route confirmed active.

---

## 2026-05-21 — Admin Collection Page: Pagination Overhaul

### Summary

تم إعادة تصميم نظام الـ Pagination في صفحة المجموعة المقتناة ليكون أكثر احترافية وأخف في الأداء.

### Changes

- Updated `forntent/src/app/admin/(dashboard)/artifacts/page.tsx`
  - Changed from server-side pagination (request per page) to **client-side pagination**.
  - Fetches only the first **30 artifacts** in a single request on page load (`getAdminArtifacts(1, 30)`).
  - Stores all 30 in `allArtifacts` state and slices locally per page.
  - **5 items per page** → max **6 pages** displayed.
  - Replaced the old single-page-number indicator with a **full numbered pagination bar**:
    - Shows all page numbers when ≤ 7 pages.
    - Shows ellipsis (`…`) for large page ranges (e.g. `1 … 4 5 6 … 10`).
    - Active page highlighted with gold background.
    - Previous / Next arrow buttons with disabled state.
  - Delete handler updated to recalculate total pages from local state after deletion.

### Verification

- TypeScript: `npx tsc --noEmit` → passed with zero errors.

---

## 2026-05-21 — Admin Collection Page: Edit Artifact Modal

### Summary

تم إضافة مودال تعديل القطع الأثرية بدلاً من الـ `alert` المؤقت الذي كان يظهر عند الضغط على زرار التعديل.

### API Changes

- Updated `forntent/src/lib/api.ts`
  - Added `UpdateArtifactInput` type.
  - Added `updateArtifact(id, input)` function that sends `PATCH /artifacts/{id}` to the FastAPI backend.

### Frontend Changes

- Updated `forntent/src/app/admin/(dashboard)/artifacts/page.tsx`
  - Added edit modal state: `editingItem`, `editForm`, `editSaving`, `editMsg`.
  - Added `openEdit(item)` — opens modal pre-filled with artifact's current data.
  - Added `handleSaveEdit()` — calls `updateArtifact`, then updates local state instantly (no reload).
  - Edit button now calls `openEdit(item)` instead of `alert()`.
  - Modal UI includes:
    - 5 editable fields: Name (EN), Name (AR), Section (EN), Section (AR), Image URL.
    - Save / Cancel buttons with loading state.
    - Green success message on save, red error message on failure.
    - Auto-closes after 900ms on success.
    - Click outside backdrop to dismiss.
  - Added localization strings for all modal text in both `en` and `ar`.

### Verification

- TypeScript: `npx tsc --noEmit` → passed with zero errors.

---

## 2026-05-21 — Image Upload to Supabase Storage

### Summary

تم إضافة وظيفة رفع الصور إلى Supabase Storage في كلٍّ من مودال التعديل وصفحة الإضافة الجديدة.

### API Changes

- Updated `forntent/src/lib/api.ts`
  - Added `IMAGE_BUCKET = "artifact-images"` constant.
  - Added `uploadImage(file: File): Promise<string>` function:
    - Generates a unique filename using `Date.now()` + random suffix.
    - Uploads to Supabase Storage bucket `artifact-images`.
    - Returns the public URL of the uploaded image.

### Frontend Changes

- Updated `forntent/src/app/admin/(dashboard)/artifacts/page.tsx` (Edit Modal)
  - Added `imgUploading` state and `editFileRef` ref.
  - Added `handleImgUpload(file)` function.
  - Image URL field now has a dedicated **Upload button** (🔼) beside it.
  - Clicking Upload opens a hidden `<input type="file" accept="image/*">`.
  - Shows spinner while uploading; auto-fills URL field on success.
  - Shows a **16×16 thumbnail preview** below the image field.

- Updated `forntent/src/app/admin/(dashboard)/artifacts/new/page.tsx` (Add Artifact)
  - Added `imagePreview`, `uploading`, `uploadedUrl` states and `fileInputRef`, `imageUrlInputRef` refs.
  - Added `handleFileSelect(file)` function.
  - The decorative Dropzone is now **fully functional**:
    - Click to browse, or **drag & drop** an image file.
    - Shows an instant local **preview** (object URL) before upload completes.
    - Spinner shown during upload; green ✓ shown on success.
    - Auto-fills the Image URL input field after upload.
  - Image URL input wired to `imageUrlInputRef` for programmatic filling.
  - `handleSubmit` falls back to `uploadedUrl` if the URL text field is empty.

### Infrastructure Requirement

> ⚠️ A Supabase Storage bucket named **`artifact-images`** must exist and be set to **Public** for images to be accessible. Create it from: Supabase Dashboard → Storage → New Bucket → `artifact-images` → enable Public.

### Verification

- TypeScript: `npx tsc --noEmit` → passed with zero errors.
