You are an expert AI system architect and senior Python developer. I need you to update and improve an existing Agentic RAG system for a museum chatbot — my graduation project.

Below I will describe what was already built, then what needs to change. Follow the delta carefully — do not rewrite things that are still valid.

---

## WHAT ALREADY EXISTS (keep as-is unless told otherwise)

### Project Context
- **Museum:** Bibliotheca Alexandrina Antiquities Museum
- **Dataset:** CSV with 97 artifacts — columns: Section Number, Section Name (AR/EN), Artifact Name (AR/EN), Description (AR/EN), Category (AR/EN), Discovery Site (AR/EN), Hall (AR/EN), Link
- **Language:** Bilingual Arabic + English, auto-detect and respond in same language

### Tech Stack — keep all of this
- **LLM:** Groq API — `llama-3.1-70b-versatile`
- **Embeddings:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Vector Store:** ChromaDB (local, persistent)
- **STT:** Groq Whisper API — `whisper-large-v3`
- **TTS:** Edge TTS — `ar-EG-SalmaNeural` for Arabic, `en-US-JennyNeural` for English
- **API Framework:** FastAPI with async support

### Indexing Pipeline — keep as-is
Script `scripts/index_artifacts.py`:
1. Loads CSV
2. Creates combined text chunk per artifact: Name (AR/EN), Category, Hall, Discovery Site, Description (first 1000 chars)
3. Generates multilingual embeddings
4. Stores in ChromaDB with full metadata
5. Handles Arabic UTF-8 correctly

### FastAPI Endpoints — keep as-is
```
POST /chat           — Text query → RAG response + artifact references
POST /voice          — Audio file → STT → RAG → TTS → returns MP3
GET  /artifacts      — List all artifacts with pagination
GET  /artifacts/{id} — Single artifact details
GET  /search         — Quick semantic search
GET  /health         — Health check
```

### Voice Pipeline — keep as-is
```python
async def text_to_speech(text: str, language: str) -> bytes:
    voice = "ar-EG-SalmaNeural" if language == "ar" else "en-US-JennyNeural"
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data
```

### System Prompts — keep as-is
**English:** "Alex" — expert museum guide AI, cite artifact name and hall, don't hallucinate
**Arabic:** "إسكندر" — نفس الشخصية بالعربي

### Environment Variables — keep as-is
```
GROQ_API_KEY=your_groq_api_key_here
CHROMA_PERSIST_DIR=./data/chroma_db
CSV_DATA_PATH=./data/bibalex_full_museum_data.csv
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
TOP_K_RESULTS=5
MAX_AGENT_ITERATIONS=3
API_HOST=0.0.0.0
API_PORT=8000
```

---

## WHAT NEEDS TO CHANGE

### 1. REMOVE — Agent Framework
**Remove completely:**
- The old single-agent custom loop (`agent.py` with `run_agent` function)
- The old tools system (`tools.py` with `search_artifacts`, `get_artifact_details`, `list_by_category`, `general_museum_info`)
- `intent.py` — intent detection is no longer a separate module
- The old `agent/` folder structure entirely

**Reason:** Replacing with LangGraph 3-node Corrective RAG graph.

---

### 2. ADD — LangGraph Corrective RAG Pipeline

**Add to requirements.txt:**
```
langgraph>=0.1.0
langchain-core>=0.2.0
```

**New folder structure for the agent layer:**
```
app/
└── graph/
    ├── __init__.py
    ├── state.py        # TypedDict for shared graph state
    ├── nodes.py        # The 3 node functions
    ├── edges.py        # Conditional edge logic (relevance check)
    └── graph.py        # Builds and compiles the StateGraph
```

---

### 3. IMPLEMENT — The 3 LangGraph Nodes

#### State Definition (`state.py`)
```python
from typing import TypedDict, List, Optional

class GraphState(TypedDict):
    original_query: str          # never modified
    rewritten_query: str         # updated by rewriter node
    language: str                # "ar" or "en"
    retrieved_docs: List[dict]   # artifacts from ChromaDB
    relevance_score: float       # 0.0 to 1.0, set by retriever node
    generation: str              # final answer, set by generator node
    rewrite_count: int           # tracks how many rewrites happened
```

#### Node 1 — Query Rewriter (`nodes.py` → `rewrite_query`)
- Takes `original_query` from state
- Calls Groq LLM with this prompt:
  ```
  You are a search query optimizer for a museum database.
  Rewrite the following user question into a clear, keyword-rich search query
  optimized for semantic vector search over museum artifact descriptions.
  Keep it concise (max 20 words). Output only the rewritten query, nothing else.
  
  Original question: {original_query}
  Rewritten query:
  ```
- Updates `rewritten_query` in state
- Also detects language and sets `language` field using langdetect

#### Node 2 — Retriever + Grader (`nodes.py` → `retrieve_and_grade`)
- Uses `rewritten_query` to search ChromaDB (top-K semantic search)
- Sets `retrieved_docs` in state
- Then calls Groq LLM to grade relevance:
  ```
  You are a relevance grader. Given a user query and a list of retrieved museum artifacts,
  output a single float between 0.0 and 1.0 representing how relevant the results are.
  1.0 = perfectly relevant, 0.0 = completely irrelevant.
  Output only the number, nothing else.
  
  Query: {rewritten_query}
  Retrieved artifacts: {retrieved_docs_summary}
  Relevance score:
  ```
- Sets `relevance_score` in state

#### Node 3 — Generator (`nodes.py` → `generate_answer`)
- Only reached when relevance_score >= 0.5 OR rewrite_count >= 2 (max retries)
- Takes `retrieved_docs` + `original_query` + `language`
- Calls Groq LLM with the appropriate system prompt (Alex/إسكندر)
- Builds context from retrieved artifacts and generates final answer
- Always includes: artifact name, hall, and link when referencing specific artifacts
- Sets `generation` in state

---

### 4. IMPLEMENT — Conditional Edges (`edges.py`)

```python
def should_rewrite(state: GraphState) -> str:
    """
    After retriever node:
    - If relevance_score < 0.5 AND rewrite_count < 2 → go to rewriter again
    - Otherwise → go to generator
    """
    if state["relevance_score"] < 0.5 and state["rewrite_count"] < 2:
        return "rewrite"
    return "generate"
```

---

### 5. IMPLEMENT — Graph Assembly (`graph.py`)

```python
from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import rewrite_query, retrieve_and_grade, generate_answer
from .edges import should_rewrite

def build_graph():
    graph = StateGraph(GraphState)
    
    graph.add_node("rewriter", rewrite_query)
    graph.add_node("retriever", retrieve_and_grade)
    graph.add_node("generator", generate_answer)
    
    graph.set_entry_point("rewriter")
    graph.add_edge("rewriter", "retriever")
    graph.add_conditional_edges("retriever", should_rewrite, {
        "rewrite": "rewriter",
        "generate": "generator"
    })
    graph.add_edge("generator", END)
    
    return graph.compile()

rag_graph = build_graph()
```

---

### 6. UPDATE — FastAPI chat and voice routes

In `app/api/routes/chat.py` and `voice.py`, replace the old `run_agent(...)` call with:

```python
from app.graph.graph import rag_graph
from app.graph.state import GraphState

async def run_rag(query: str) -> dict:
    initial_state: GraphState = {
        "original_query": query,
        "rewritten_query": "",
        "language": "en",
        "retrieved_docs": [],
        "relevance_score": 0.0,
        "generation": "",
        "rewrite_count": 0
    }
    result = await rag_graph.ainvoke(initial_state)
    return {
        "answer": result["generation"],
        "language": result["language"],
        "rewrite_count": result["rewrite_count"],
        "retrieved_docs": result["retrieved_docs"]
    }
```

---

### 7. UPDATED PROJECT STRUCTURE

```
bibalex_museum_rag/
├── main.py
├── .env.example
├── requirements.txt
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   │
│   ├── graph/                  ← NEW (replaces agent/)
│   │   ├── __init__.py
│   │   ├── state.py            ← GraphState TypedDict
│   │   ├── nodes.py            ← 3 node functions
│   │   ├── edges.py            ← conditional edge logic
│   │   └── graph.py            ← builds compiled graph
│   │
│   ├── rag/                    ← unchanged
│   │   ├── __init__.py
│   │   ├── embedder.py
│   │   ├── vectorstore.py
│   │   └── retriever.py
│   │
│   ├── voice/                  ← unchanged
│   │   ├── __init__.py
│   │   ├── stt.py
│   │   └── tts.py
│   │
│   ├── api/                    ← routes updated to use graph
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── voice.py
│   │   │   └── artifacts.py
│   │   └── middleware.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── language.py
│       └── helpers.py
│
├── data/
│   ├── bibalex_full_museum_data.csv
│   ├── chroma_db/
│   └── museum_general_info.json
│
└── scripts/
    ├── index_artifacts.py      ← unchanged
    └── test_rag.py             ← update to test the graph flow
```

---

### 8. UPDATED REQUIREMENTS.TXT

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
groq>=0.4.0
chromadb>=0.4.22
sentence-transformers>=2.6.0
edge-tts>=6.1.9
pandas>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.9
langdetect>=1.0.9
httpx>=0.27.0
numpy>=1.24.0
langgraph>=0.1.0
langchain-core>=0.2.0
```

---

## DELIVERABLES

Generate only the files that changed or are new:
1. `app/graph/state.py` — full implementation
2. `app/graph/nodes.py` — full implementation of all 3 nodes
3. `app/graph/edges.py` — full implementation
4. `app/graph/graph.py` — full implementation
5. `app/api/routes/chat.py` — updated to use graph
6. `app/api/routes/voice.py` — updated to use graph
7. `requirements.txt` — updated
8. `scripts/test_rag.py` — updated to test graph with sample Arabic and English queries
9. `README.md` — update only the architecture section to describe the 3-node Corrective RAG flow

Do not regenerate files that have not changed (rag/, voice/, utils/, config.py, models.py, middleware.py, index_artifacts.py).

Implement each file fully. No placeholder comments. Production-quality code.
