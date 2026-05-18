You are an expert AI system architect and senior Python developer. I need you to design and implement a complete, production-ready Agentic RAG system for a museum chatbot — my graduation project. Read every requirement carefully and produce a full, structured implementation.

---

## PROJECT CONTEXT

**Museum:** Bibliotheca Alexandrina Antiquities Museum  
**Dataset:** A CSV with 97 museum artifacts containing these columns:
- Section Number, Section Name (Arabic/English)
- Artifact Name (Arabic/English)
- Description (Arabic/English) — very long, rich academic text
- Category (Arabic/English)
- Discovery Site (Arabic/English)
- Hall (Arabic/English)
- Link (URL to artifact page)

**Language:** The system must handle BOTH Arabic and English queries seamlessly. Auto-detect the query language and respond in the same language.

---

## SYSTEM ARCHITECTURE REQUIREMENTS

### 1. TECH STACK (STRICT — do not substitute)
- **LLM:** Groq API — use `llama-3.1-70b-versatile` as primary model
- **Embeddings:** Use `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (supports Arabic + English)
- **Vector Store:** ChromaDB (local, persistent)
- **STT (Speech-to-Text):** Groq Whisper API (`whisper-large-v3`)
- **TTS (Text-to-Speech):** Edge TTS library (`edge-tts` Python package) — use `ar-EG-SalmaNeural` for Arabic, `en-US-JennyNeural` for English
- **API Framework:** FastAPI with async support
- **Agent Framework:** Build a custom lightweight agentic loop (do NOT use LangChain or LlamaIndex)

---

### 2. AGENTIC RAG DESIGN

The agent must have access to the following **tools** and decide which to use based on the query:

**Tool 1: `search_artifacts`**
- Semantic vector search over artifact descriptions and names
- Returns top-K relevant artifacts with metadata
- Supports filtering by: hall, category, discovery site, section

**Tool 2: `get_artifact_details`**  
- Retrieves full artifact details by name or ID
- Returns complete description, discovery site, hall, category, link

**Tool 3: `list_by_category`**
- Lists all artifacts in a specific category or hall
- Useful for "show me everything in Hall X" queries

**Tool 4: `general_museum_info`**
- Answers general questions about the museum using a static knowledge base
- Covers: museum history, opening hours, location, sections overview

**Agentic Loop:**
```
User Query → Intent Detection → Tool Selection → Tool Execution → 
Result Synthesis → Response Generation → (Optional: Follow-up Tool Call)
```
The agent can call multiple tools in sequence if needed (multi-hop reasoning).

---

### 3. INDEXING PIPELINE

Build a script `scripts/index_artifacts.py` that:
1. Loads the CSV file
2. For each artifact, creates a combined text chunk:
   ```
   Name: {artifact_name_en} / {artifact_name_ar}
   Category: {category_en}
   Hall: {hall_en}
   Discovery Site: {discovery_site_en}
   Description: {description_en[:1000]}  # truncate for embedding
   ```
3. Generates multilingual embeddings
4. Stores in ChromaDB with full metadata as payload
5. Creates separate collections for Arabic and English OR uses one unified collection with language metadata
6. Prints indexing progress and final stats

---

### 4. FASTAPI ENDPOINTS

```
POST /chat           — Text query, returns text response + artifact references
POST /voice          — Accepts audio file (WAV/MP3), runs STT → RAG → TTS, returns audio
GET  /artifacts      — List all artifacts with pagination
GET  /artifacts/{id} — Get single artifact details
GET  /search         — Quick semantic search endpoint
GET  /health         — Health check
```

**Voice endpoint flow:**
1. Receive audio file
2. Transcribe with Groq Whisper
3. Run through Agentic RAG
4. Convert response to speech with Edge TTS
5. Return audio file (MP3) as streaming response

---

### 5. PROJECT STRUCTURE

Generate EXACTLY this structure:

```
bibalex_museum_rag/
├── main.py                    # FastAPI app entry point
├── .env.example               # Environment variables template
├── requirements.txt           # All dependencies with versions
├── README.md                  # Setup and usage instructions
│
├── app/
│   ├── __init__.py
│   ├── config.py              # Settings using pydantic-settings
│   ├── models.py              # Pydantic request/response models
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py           # Main agentic loop
│   │   ├── tools.py           # All tool definitions and implementations
│   │   ├── prompts.py         # System prompts (Arabic + English)
│   │   └── intent.py          # Intent detection logic
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embedder.py        # Multilingual embedding logic
│   │   ├── vectorstore.py     # ChromaDB operations
│   │   └── retriever.py       # Semantic search + hybrid search
│   │
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── stt.py             # Groq Whisper STT
│   │   └── tts.py             # Edge TTS wrapper
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── chat.py        # /chat endpoint
│   │   │   ├── voice.py       # /voice endpoint
│   │   │   └── artifacts.py   # /artifacts endpoints
│   │   └── middleware.py      # CORS, logging middleware
│   │
│   └── utils/
│       ├── __init__.py
│       ├── language.py        # Language detection utility
│       └── helpers.py         # Misc helpers
│
├── data/
│   ├── bibalex_full_museum_data.csv
│   ├── chroma_db/             # Persistent vector store (auto-created)
│   └── museum_general_info.json  # Static museum knowledge base
│
└── scripts/
    ├── index_artifacts.py     # Run once to build vector index
    └── test_rag.py            # Quick CLI test script
```

---

### 6. SYSTEM PROMPTS

The agent must have two system prompts — one per language:

**English System Prompt:**
```
You are "Alex", an expert museum guide AI for the Bibliotheca Alexandrina Antiquities Museum.
You help visitors explore artifacts from Ancient Egyptian, Greco-Roman, and other collections.
You have access to tools to search the museum database. Always cite the artifact name and hall
when referencing specific objects. Be informative, engaging, and historically accurate.
If you cannot find relevant information, say so honestly rather than hallucinating.
Respond in English.
```

**Arabic System Prompt:**
```
أنت "إسكندر"، مرشد متحف ذكاء اصطناعي خبير في متحف آثار مكتبة الإسكندرية.
تساعد الزوار على استكشاف القطع الأثرية من مجموعات مصر القديمة واليونانية الرومانية وغيرها.
لديك أدوات للبحث في قاعدة بيانات المتحف. اذكر دائمًا اسم القطعة والقاعة عند الإشارة إلى أي قطعة.
كن مفيدًا وجذابًا ودقيقًا تاريخيًا. إذا لم تجد معلومات ذات صلة، قل ذلك بصدق.
أجب باللغة العربية.
```

---

### 7. KEY IMPLEMENTATION DETAILS

**Groq Client setup:**
```python
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
```

**Groq Whisper STT:**
```python
with open(audio_file, "rb") as f:
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=f,
        response_format="text"
    )
```

**Edge TTS usage:**
```python
import edge_tts
import asyncio

async def text_to_speech(text: str, language: str) -> bytes:
    voice = "ar-EG-SalmaNeural" if language == "ar" else "en-US-JennyNeural"
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data
```

**Agentic loop pattern:**
```python
async def run_agent(query: str, language: str, max_iterations: int = 3):
    messages = [{"role": "system", "content": get_system_prompt(language)}]
    messages.append({"role": "user", "content": query})
    
    for iteration in range(max_iterations):
        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            tools=get_tool_schemas(),
            tool_choice="auto"
        )
        
        if response.choices[0].finish_reason == "stop":
            return response.choices[0].message.content
            
        # Handle tool calls
        tool_calls = response.choices[0].message.tool_calls
        for tool_call in tool_calls:
            result = await execute_tool(tool_call.function.name, tool_call.function.arguments)
            messages.append({"role": "tool", "content": str(result), "tool_call_id": tool_call.id})
    
    return response.choices[0].message.content
```

---

### 8. ENVIRONMENT VARIABLES (.env.example)
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

### 9. REQUIREMENTS.TXT (include these exact packages)
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
```

---

### 10. DELIVERABLES

Generate ALL of the following:
1. Complete implementation of every Python file listed in the project structure
2. Working `requirements.txt`
3. `.env.example`
4. `README.md` with: setup instructions, how to index data, how to run the API, example curl commands for all endpoints
5. `data/museum_general_info.json` with static facts about Bibliotheca Alexandrina museum
6. Make sure all async functions use `async/await` properly throughout
7. Add proper error handling with HTTP exceptions
8. Add request/response logging middleware
9. The indexing script must handle Arabic text correctly (UTF-8)
10. The `/voice` endpoint must return actual playable audio

Do not skip any file. Implement each file fully — no placeholder comments like "# implement this later". Write production-quality code.
