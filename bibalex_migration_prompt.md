You are an expert Python developer. I have an existing museum chatbot codebase that I want to migrate and upgrade. Below I will show you the OLD code in full, then describe exactly what to keep, what to change, and what the new architecture should be.

Read everything carefully before writing a single line of code.

---

## PART 1 — WHAT THE OLD CODE DOES (understand this first)

The old code is a **Streamlit app** with a **LangGraph 3-node pipeline**. Here is what each part does:

### Old Prompts (`prompts.py`)
- `REWRITE_PROMPT`: Rewrites the user query into a standalone question based on chat history. Resolves pronouns, contextualizes, keeps same language.
- `SYSTEM_PROMPT`: Museum guide persona. Conversational, concise, voice-friendly. Handles greetings. Responds in user's language. Says "I'm not sure" when context doesn't have the answer.
- `query_rewrite_extend()`: Builds the full rewrite prompt string with history + query
- `system_prompt_extend()`: Builds the full generation prompt string with context + history + query
- `_format_chat_history()`: Formats chat history list into "Role: content" string, handles both dict and object formats

### Old State (`models.py`)
```python
class State(TypedDict):
    chat_history: Annotated[list, add_messages]
    query: str
    context: Optional[list[str]]
    response: str
    rewritten_query: str
```

### Old Agents (`agents.py`)
- `rewrite_query_agent`: Takes `query` + `chat_history` → calls Groq LLM → returns `rewritten_query`
- `retriever_agent`: Takes `rewritten_query` → calls ChromaDB retriever (k=3) → returns `context`
- `response_agent`: Takes `rewritten_query` + `chat_history` + `context` → calls Groq LLM → returns `response`
- Model used: `llama-3.3-70b-versatile`
- Embeddings: `BAAI/bge-small-en-v1.5`
- All clients initialized globally (performance optimization — keep this pattern)

### Old Workflow (`workflow.py`)
- Simple LangGraph: START → rewrite_query → retriever_agent → response_agent → END
- No conditional edges, no relevance grading
- Graph compiled once globally

### Old DB Creation (`create_db.py`)
- Reads `Artifact.xlsx`
- Creates one Document per row: all columns joined as "col: value\n"
- Metadata: `row_id`, `image`, `name_ar`, `name_en`
- Image path resolved from local folder `"image for museum"` with fallback to URL

### Old UI (`app_ui.py`)
- **Streamlit** multi-page app
- 6 screens: welcome → sections → items → details → answer → chat
- Features: FAQ sidebar, TTS (edge-tts), STT (Groq Whisper), image display, chat history, session logging
- Data loaded from `dataset_with_images.csv` (columns: Name_AR, Name_EN, Description_AR, Description_EN, Image_URL, Hall_ID)
- Gold + dark theme with Cairo font

---

## PART 2 — THE NEW DATASET

The old data was `Artifact.xlsx` / `dataset_with_images.csv`.
The new data is `bibalex_full_museum_data.csv` with these columns:

```
Section Number, Section Name Arabic, Section Name English,
Artifact Name Arabic, Artifact Name English,
Description Arabic, Description English,
Category Arabic, Category English,
Discovery site Arabic, Discovery Site English,
Hall Arabic, Hall English,
Link
```

97 artifacts total. No local images — use the `Link` column which points to the BibaAlex website artifact page. For images, construct the image URL from the artifact page or use a placeholder.

---

## PART 3 — NEW ARCHITECTURE (what to build)

### Overview
- **Keep:** The RAG logic, prompts style, LangGraph pipeline, TTS/STT, bilingual support, gold/dark theme
- **Upgrade:** Add relevance grading (Corrective RAG), replace Streamlit with FastAPI, adapt to new dataset
- **Remove:** Streamlit UI code, FAQ sidebar, `screen_answer` page, `Artifact.xlsx` references, `dataset_with_images.csv` references, local image folder logic

---

### Tech Stack
```
Python 3.11+
FastAPI + uvicorn          (replaces Streamlit)
LangGraph >= 0.1.0
langchain-groq
langchain-huggingface
langchain-chroma
langchain-core
groq                       (for Whisper STT)
edge-tts                   (TTS, same as before)
sentence-transformers
chromadb
pandas
pydantic + pydantic-settings
python-multipart
langdetect
python-dotenv
```

---

### Project Structure

```
bibalex_museum_rag/
├── main.py                        # FastAPI entry point
├── .env.example
├── requirements.txt
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── config.py                  # pydantic-settings
│   ├── models.py                  # Pydantic API models + GraphState
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py               # GraphState TypedDict (upgraded from old State)
│   │   ├── prompts.py             # KEEP old prompts logic, adapt for new system
│   │   ├── nodes.py               # 3 nodes: rewriter, retriever+grader, generator
│   │   ├── edges.py               # Conditional edge: relevance check
│   │   └── graph.py               # Builds and compiles StateGraph
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embedder.py            # HuggingFace embeddings (global init)
│   │   ├── vectorstore.py         # ChromaDB operations
│   │   └── retriever.py           # Retriever wrapper
│   │
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── stt.py                 # Groq Whisper (keep old logic)
│   │   └── tts.py                 # Edge TTS (keep old logic)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── chat.py            # POST /chat
│   │   │   ├── voice.py           # POST /voice
│   │   │   └── artifacts.py       # GET /artifacts, /search
│   │   └── middleware.py          # CORS + logging
│   │
│   └── utils/
│       ├── __init__.py
│       ├── language.py            # Language detection
│       └── helpers.py
│
├── data/
│   ├── bibalex_full_museum_data.csv
│   └── chroma_db/                 # auto-created
│
└── scripts/
    ├── index_artifacts.py         # Index new CSV into ChromaDB
    └── test_rag.py                # CLI test
```

---

### GraphState (upgraded from old `State`)

```python
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import add_messages

class GraphState(TypedDict):
    # Kept from old State
    chat_history: Annotated[list, add_messages]
    query: str                        # original user query
    rewritten_query: str
    context: Optional[List[dict]]     # retrieved docs from ChromaDB
    response: str                     # final answer

    # New fields for Corrective RAG
    language: str                     # "ar" or "en"
    relevance_score: float            # 0.0 to 1.0
    rewrite_count: int                # max 2 rewrites
```

---

### Prompts (`app/graph/prompts.py`)

**KEEP the exact spirit and instructions of the old prompts.** Just adapt:

`REWRITE_PROMPT` — keep exactly as is. It already handles chat history context resolution perfectly.

`SYSTEM_PROMPT` — keep exactly as is. The concise, conversational, voice-friendly museum guide persona is the core of the product. Just update the museum name references from "NMEC" to "Bibliotheca Alexandrina Antiquities Museum".

Add a new prompt `RELEVANCE_GRADE_PROMPT`:
```
You are a relevance grader for a museum knowledge base.
Given a user query and retrieved museum artifact documents, output a single float between 0.0 and 1.0.
1.0 = the retrieved documents perfectly answer the query.
0.0 = completely irrelevant.
Output ONLY the number. Nothing else. No explanation.

Query: {query}
Retrieved documents summary: {docs_summary}
Relevance score:
```

Keep `query_rewrite_extend()`, `system_prompt_extend()`, and `_format_chat_history()` functions exactly — they work well.

---

### Nodes (`app/graph/nodes.py`)

**Node 1 — `rewrite_query_node`** (upgraded from old `rewrite_query_agent`):
- Same logic as old `rewrite_query_agent` — uses REWRITE_PROMPT + `query_rewrite_extend()`
- Additionally: detect language of original query using `langdetect`, set `language` in state
- Set `rewrite_count` += 1 on each call
- On error: fallback to original query (same as old code)

**Node 2 — `retrieve_and_grade_node`** (new, replaces old `retriever_agent`):
- Use `rewritten_query` to search ChromaDB (k=3, same as old)
- Store results in `context`
- Then call Groq LLM with `RELEVANCE_GRADE_PROMPT` to grade relevance
- Parse response as float, clamp to [0.0, 1.0], store in `relevance_score`
- On parse error: default score = 0.6 (pass through)

**Node 3 — `generate_response_node`** (upgraded from old `response_agent`):
- Same logic as old `response_agent` — uses SYSTEM_PROMPT + `system_prompt_extend()`
- Use `rewritten_query` as the query (same as old)
- Pass `chat_history` and `context` (same as old)
- On error: return friendly error message (same as old)

---

### Edges (`app/graph/edges.py`)

```python
def should_rewrite(state: GraphState) -> str:
    if state["relevance_score"] < 0.5 and state["rewrite_count"] < 2:
        return "rewrite"
    return "generate"
```

---

### Graph (`app/graph/graph.py`)

```
START → rewrite_query_node → retrieve_and_grade_node
retrieve_and_grade_node → [conditional] → rewrite_query_node (if rewrite)
                                        → generate_response_node (if generate)
generate_response_node → END
```

Compile graph once globally at module level (same pattern as old `app_workflow = build_workflow()`).

---

### LLM + Embeddings Initialization

**Keep the old pattern of global initialization** — it was explicitly marked as a performance optimization in the old code. Initialize once at module level:

```python
# In app/rag/embedder.py
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=...)
embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
```

Note: keep `BAAI/bge-small-en-v1.5` — the old codebase used it and it works for this project.

---

### STT (`app/voice/stt.py`)

**Keep the exact old `transcribe_audio_groq()` logic** including:
- Groq Whisper `whisper-large-v3`
- `response_format="json"`, `temperature=0.0`
- Language parameter support
- The artifact name correction logic structure (but simplify — remove dependency on `artifact_names.py`, just do basic transcription for now)

---

### TTS (`app/voice/tts.py`)

**Keep the same voice mapping:**
```python
VOICE_MAPPING = {
    "ar": "ar-EG-SalmaNeural",
    "en": "en-US-JennyNeural"
}
```

Keep `generate_audio()` as async function using edge-tts, same as old `tts_engine.py`.

---

### Indexing Script (`scripts/index_artifacts.py`)

Adapted for the new CSV. For each artifact row, create a Document with:
```
page_content:
  "Artifact: {Artifact Name English} / {Artifact Name Arabic}
   Category: {Category English}
   Hall: {Hall English}
   Discovery Site: {Discovery Site English}
   Description: {Description English[:1000]}
   Description AR: {Description Arabic[:500]}"

metadata:
  artifact_id: slugified name
  artifact_name_en: ...
  artifact_name_ar: ...
  section_number: ...
  section_name_en: ...
  hall_en: ...
  hall_ar: ...
  category_en: ...
  discovery_site_en: ...
  link: ...
```

Print progress same as old code (every 32 docs).

---

### FastAPI Routes

**`POST /chat`**
Request:
```json
{
  "query": "string",
  "chat_history": [{"role": "user", "content": "..."}]  // optional
}
```
Response:
```json
{
  "response": "string",
  "language": "en",
  "rewrite_count": 1,
  "pipeline": "corrective_rag",
  "artifact_references": [...]
}
```

Flow:
1. Build initial `GraphState` with query + chat_history
2. `await rag_graph.ainvoke(initial_state)`
3. Return response + metadata

**`POST /voice`**
- Accept audio file (`UploadFile`)
- Save to temp file
- Call `transcribe_audio_groq(temp_path, language=None)` — auto-detect language
- Run through RAG graph
- Generate TTS audio with `generate_audio()`
- Return MP3 as `StreamingResponse`

**`GET /artifacts`** — list with pagination, optional `?section=` filter
**`GET /artifacts/{artifact_id}`** — single artifact
**`GET /search`** — `?q=query&top_k=5` semantic search
**`GET /health`** — health check

---

### Session Logging

**Keep the old `log_interaction()` logic** — log to `session_logs.jsonl`:
```python
def log_interaction(query, response, context, latency=0.0):
    log_entry = {
        "query": query,
        "response": response,
        "context": [doc.page_content for doc in context if hasattr(doc, 'page_content')],
        "latency": latency
    }
    with open("session_logs.jsonl", "a", encoding="utf-8") as f:
        json.dump(log_entry, f, ensure_ascii=False)
        f.write("\n")
```

Call this from the `/chat` route after getting a response.

---

### Environment Variables (`.env.example`)

```
GROQ_API_KEY=your_groq_api_key_here
CHROMA_PERSIST_DIR=./data/chroma_db
CSV_DATA_PATH=./data/bibalex_full_museum_data.csv
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
TOP_K_RESULTS=3
MAX_REWRITE_ATTEMPTS=2
API_HOST=0.0.0.0
API_PORT=8000
```

---

### requirements.txt

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
groq>=0.4.0
langchain-groq>=0.1.0
langchain-huggingface>=0.0.3
langchain-chroma>=0.1.0
langchain-core>=0.2.0
langgraph>=0.1.0
chromadb>=0.4.22
sentence-transformers>=2.6.0
edge-tts>=6.1.9
pandas>=2.0.0
openpyxl>=3.1.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.9
langdetect>=1.0.9
httpx>=0.27.0
numpy>=1.24.0
python-dotenv>=1.0.0
Pillow>=10.0.0
```

---

## DELIVERABLES

Generate ALL files completely:

1. `main.py`
2. `app/config.py`
3. `app/models.py`
4. `app/graph/state.py`
5. `app/graph/prompts.py` ← keep old prompts spirit, adapt museum name
6. `app/graph/nodes.py` ← keep old agent logic, add grading
7. `app/graph/edges.py`
8. `app/graph/graph.py`
9. `app/rag/embedder.py` ← global init pattern from old code
10. `app/rag/vectorstore.py`
11. `app/rag/retriever.py`
12. `app/voice/stt.py` ← keep old transcription logic
13. `app/voice/tts.py` ← keep old TTS logic + VOICE_MAPPING
14. `app/api/routes/chat.py` ← includes log_interaction
15. `app/api/routes/voice.py`
16. `app/api/routes/artifacts.py`
17. `app/api/middleware.py`
18. `app/utils/language.py`
19. `app/utils/helpers.py`
20. `scripts/index_artifacts.py`
21. `scripts/test_rag.py`
22. `.env.example`
23. `requirements.txt`
24. `README.md`

All `__init__.py` files as needed.

**Rules:**
- No placeholder comments like "# implement this later"
- Keep all global initialization patterns from old code (performance matters)
- The prompts MUST keep the exact instructions and style from the old REWRITE_PROMPT and SYSTEM_PROMPT
- Handle Arabic text with UTF-8 throughout
- All async functions use `async/await` properly
- Proper error handling with HTTP exceptions and fallbacks (same defensive style as old code)
