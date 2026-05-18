# 🏛️ Bibliotheca Alexandrina Museum RAG API

A **Corrective RAG** chatbot powered by **LangGraph** for the **Bibliotheca Alexandrina Antiquities Museum**. Supports both **Arabic** and **English** queries via text and voice.

---

## ✨ Features

- 🔄 **LangGraph Corrective RAG** — 3-node pipeline: Query Rewriter → Retriever+Grader → Generator
- 🔍 **Semantic Search** — Multilingual embeddings (Arabic + English) via ChromaDB
- 🎙️ **Voice Interface** — Groq Whisper STT → Corrective RAG → Edge TTS response
- 🌐 **Bilingual** — Auto-detects language; responds as "Alex" (EN) or "إسكندر" (AR)
- ⚡ **FastAPI** — Async API with full OpenAPI documentation

---

## 🗂️ Project Structure

```
bibalex_museum_rag/
├── main.py                    # FastAPI app entry point
├── .env.example               # Environment variables template
├── requirements.txt           # All dependencies
├── README.md
│
├── app/
│   ├── config.py              # Settings (pydantic-settings)
│   ├── models.py              # Pydantic request/response models
│   │
│   ├── graph/                 # LangGraph Corrective RAG pipeline
│   │   ├── state.py           # GraphState TypedDict
│   │   ├── nodes.py           # 3 node functions (rewriter, retriever, generator)
│   │   ├── edges.py           # Conditional edge logic (relevance check)
│   │   └── graph.py           # Builds & compiles the StateGraph
│   │
│   ├── rag/
│   │   ├── embedder.py        # Multilingual embedding (sentence-transformers)
│   │   ├── vectorstore.py     # ChromaDB operations
│   │   └── retriever.py       # Semantic search
│   │
│   ├── voice/
│   │   ├── stt.py             # Groq Whisper STT
│   │   └── tts.py             # Edge TTS wrapper
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py        # POST /chat
│   │   │   ├── voice.py       # POST /voice
│   │   │   └── artifacts.py   # GET /artifacts, /search
│   │   └── middleware.py      # CORS + request logging
│   │
│   └── utils/
│       ├── language.py        # Language detection
│       └── helpers.py         # Text utilities
│
├── data/
│   ├── bibalex_full_museum_data.csv
│   ├── chroma_db/             # ChromaDB persistent store (auto-created)
│   └── museum_general_info.json
│
└── scripts/
    ├── index_artifacts.py     # Run once to build vector index
    └── test_rag.py            # CLI test script
```

---

## 🚀 Setup

### 1. Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com/)

### 2. Install dependencies

```bash
cd bibalex_museum_rag
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 4. Index the artifacts (run once)

This downloads the embedding model (~100MB) and indexes all 97 artifacts:

```bash
python scripts/index_artifacts.py
```

Expected output:
```
Loaded 97 rows from CSV.
After filtering: 97 valid artifact rows.
Progress: 32/97 artifacts embedded (33%)
Progress: 64/97 artifacts embedded (66%)
Progress: 97/97 artifacts embedded (100%)
Storing 97 documents in ChromaDB...
Indexing complete! Total artifacts in ChromaDB: 97
```

### 5. Run the API

```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs at: **http://localhost:8000/docs**

---

## 📡 API Endpoints

### `POST /chat` — Text chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about the Isis statuette"}'
```

```bash
# Arabic query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "أخبرني عن تمثال إيزيس"}'
```

**Response:**
```json
{
  "response": "The Isis statuette is a bronze figurine...",
  "language": "en",
  "artifact_references": [
    {
      "artifact_name_en": "Statuette of Isis suckling Harpocrates",
      "artifact_name_ar": "تمثال لإيزيس وهي ترضع حربوقراط",
      "hall_en": "Greco-Roman Antiquities, showcase 15",
      "link": "https://antiquities.bibalex.org/...",
      "relevance_score": 0.92
    }
  ],
  "pipeline": "corrective_rag",
  "rewrite_count": 1
}
```

---

### `POST /voice` — Voice query (STT → RAG → TTS)

```bash
curl -X POST http://localhost:8000/voice \
  -F "file=@my_question.wav" \
  --output response.mp3
```

The endpoint:
1. Transcribes audio with Groq Whisper
2. Runs through the LangGraph Corrective RAG pipeline
3. Synthesises the answer with Edge TTS
4. Returns a streaming MP3 response

---

### `GET /artifacts` — List all artifacts

```bash
curl "http://localhost:8000/artifacts?page=1&page_size=10"
```

---

### `GET /artifacts/{id}` — Get artifact details

```bash
curl "http://localhost:8000/artifacts/artifact_0000_statuette_of_isis_suckling_harpocra"
```

---

### `GET /artifacts/search` — Semantic search

```bash
curl "http://localhost:8000/artifacts/search?q=bronze+statues&top_k=5"
curl "http://localhost:8000/artifacts/search?q=تماثيل+برونزية&top_k=5"
# With filters:
curl "http://localhost:8000/artifacts/search?q=amulets&hall=Afterlife&top_k=5"
```

---

### `GET /health` — Health check

```bash
curl http://localhost:8000/health
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq `llama-3.3-70b-versatile` |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Vector Store | ChromaDB (local, persistent) |
| STT | Groq Whisper `whisper-large-v3` |
| TTS | Edge TTS (`ar-EG-SalmaNeural` / `en-US-JennyNeural`) |
| API | FastAPI + uvicorn |
| RAG Pipeline | LangGraph `StateGraph` — Corrective RAG (3 nodes) |
| Graph Lib | `langgraph>=0.1.0` + `langchain-core>=0.2.0` |

---

## 🔄 Corrective RAG Architecture

The core pipeline is a **3-node LangGraph `StateGraph`**:

```
User Query
    │
    ▼
┌──────────┐
│ Rewriter │  Node 1 — Rewrites query for semantic search; detects language
└────┬─────┘
     │
     ▼
┌──────────────────┐
│ Retriever+Grader │  Node 2 — ChromaDB semantic search + LLM relevance grade
└────┬─────────────┘
     │
     │  relevance_score < 0.5
     │  AND rewrite_count < 2  ──────► back to Rewriter (retry)
     │
     │  relevance_score >= 0.5
     │  OR  rewrite_count >= 2
     ▼
┌───────────┐
│ Generator │  Node 3 — Synthesises bilingual answer citing name, hall & link
└───────────┘
     │
     ▼
  Final Answer (Arabic or English)
```

**Shared `GraphState` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `original_query` | `str` | Raw user query — never modified |
| `rewritten_query` | `str` | Keyword-optimised query from Node 1 |
| `language` | `str` | `"ar"` or `"en"` — detected by rewriter |
| `retrieved_docs` | `List[dict]` | Artifacts from ChromaDB |
| `relevance_score` | `float` | 0.0–1.0 assigned by grader LLM |
| `generation` | `str` | Final answer from Node 3 |
| `rewrite_count` | `int` | Number of rewrites so far (max 2) |

---

## 🧪 Quick CLI Test

```bash
# Test with default queries
python scripts/test_rag.py

# Test with a custom query
python scripts/test_rag.py "What artifacts are from Saqqara?"
python scripts/test_rag.py "ما هي القطع المكتشفة في سقارة؟"
```

---

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | **required** | Your Groq API key |
| `CHROMA_PERSIST_DIR` | `./data/chroma_db` | ChromaDB storage path |
| `CSV_DATA_PATH` | `./data/bibalex_full_museum_data.csv` | Artifact dataset |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Embedding model |
| `TOP_K_RESULTS` | `5` | Default number of search results |
| `MAX_REWRITE_ATTEMPTS` | `2` | Max query rewrites in the Corrective RAG loop |
| `API_HOST` | `0.0.0.0` | API host |
| `API_PORT` | `8000` | API port |

---

## 🌍 Bilingual Support

The system automatically detects whether a query is in Arabic or English using:
1. Unicode character analysis (Arabic script detection)
2. `langdetect` library as fallback

**Arabic persona:** "إسكندر" (Iskandar) — responds in Arabic  
**English persona:** "Alex" — responds in English
