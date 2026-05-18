#promts 
from typing import List, Any
REWRITE_PROMPT = """
You are an AI assistant specialized in rewriting user queries.
Your task is to rewrite the "Last User Query" based on the "Chat History" to make it a standalone question.

### Guidelines:
1. **Resolve Pronouns**: Replace pronouns (it, he, she, they, this) with specific names from history.
2. **Contextualize**: If the query depends on previous answers, include that context.
3. **No Answering**: Do NOT answer the question. Only rewrite it.
4. **Standalone Check**: If the query is already clear, return it as is.
5. **Language**: Keep the rewritten query in the same language as the user's original query.

### Examples:
History: User: Tell me about the Rosetta Stone. | Assistant: It is a granodiorite stele found in 1799.
Last User Query: Where was it found?
Rewritten Query: Where was the Rosetta Stone found?

History: User: Hi. | Assistant: Hello! How can I help?
Last User Query: What are the opening hours?
Rewritten Query: What are the opening hours?
"""
SYSTEM_PROMPT = """
You are a friendly and knowledgeable museum guide robot.
Your goal is to assist visitors in a natural, spoken, and human-like way.

### Instructions:
1. **Be Conversational**: Speak like a human. Use a warm, friendly tone.
2. **Be Concise (Critical)**: Keep answers short and sweet. Do NOT give essay-like responses. Direct answers are best for voice.
3. **Greetings & Courtesies**: If the user says "hi", "hello", "thanks", or "thank you", reply politely (e.g., "You're welcome!" or "Hello!"). Do not search context for these.
4. **No Unsolicited Info**: Answer ONLY what is asked. Do not list extra exhibits unless requested.
5. **Unknown Info**: If the answer is not in the <Context> below, say: "I'm not sure about that based on my current info, but I can help with other museum topics."
6. **Language**: Always respond in the same language as the user's query. If the user asks in Arabic, answer in Arabic.
"""

# ==========================================
# 2. HELPER FUNCTION (لضمان قراءة الهيستوري صح)
# ==========================================

def _format_chat_history(chat_history: List[Any]) -> str:
    """Internal helper to format history so the AI knows who is speaking."""
    history_str = ""
    if not chat_history:
        return "No previous history."

    for msg in chat_history:
        # Check if msg is a dict or an object
        if isinstance(msg, dict):
            role = msg.get('role', 'User')
            content = msg.get('content', '')
        else:
            # Handle object-based history (like LangChain)
            role = getattr(msg, 'role', getattr(msg, 'type', 'User'))
            content = getattr(msg, 'content', str(msg))
        
        # Format clearly: "User: text" to avoid confusion
        history_str += f"{role}: {content}\n"
    
    return history_str.strip()

# ==========================================
# 3. MAIN FUNCTIONS (بنفس الأسماء القديمة)
# ==========================================

def query_rewrite_extend(user_input: str, chat_history: list) -> str:
    # Use the helper to get clean history with roles
    history_str = _format_chat_history(chat_history)
    
    prompt = f"""
{REWRITE_PROMPT}

### Current Task:
Chat History:
{history_str}

Last User Query: {user_input}

Rewritten Query:
    """
    return prompt.strip()

def system_prompt_extend(user_input: str, chat_history: list, content: str) -> str:
    # Use the helper to get clean history with roles
    # Note: 'chat_history' type hint changed to list to match logic, 
    # but it handles whatever you pass correctly via the helper.
    if isinstance(chat_history, str):
         history_str = chat_history
    else:
         history_str = _format_chat_history(chat_history)

    prompt = f"""
{SYSTEM_PROMPT}

### Retrieved Context (Knowledge Base):
<Context>
{content}
</Context>

### Conversation History:
<History>
{history_str}
</History>

### User Query:
{user_input}

Response:
    """
    return prompt.strip()
#workflow 
from agents import rewrite_query_agent, response_agent, retriever_agent
from models import State
from langgraph.graph import StateGraph, START, END

# --- Global Graph Construction (Optimization) ---
# Build and compile the graph once at module level
def build_workflow():
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("rewrite_query", rewrite_query_agent)
    graph.add_node("retriever_agent", retriever_agent)
    graph.add_node("response_agent", response_agent)

    # Define edges
    graph.add_edge(START, "rewrite_query")
    graph.add_edge("rewrite_query", "retriever_agent")
    graph.add_edge("retriever_agent", "response_agent")
    graph.add_edge("response_agent", END)
    
    return graph.compile()

# Initialize the compiled graph globally
app_workflow = build_workflow()

class Workflow:
    def run(self, initial_state: State):
        # Use the globally compiled graph
        result = app_workflow.invoke(initial_state)
        return result 
      
       #agents 
       import os
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

from langchain_groq import ChatGroq
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from models import State
from dotenv import load_dotenv
from prompts import REWRITE_PROMPT, SYSTEM_PROMPT, query_rewrite_extend, system_prompt_extend

load_dotenv(override=True)

# --- Global Initialization (Critical for Performance) ---
# Initialize LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

# Initialize Embeddings globally to avoid reloading on every request
embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)

# Initialize Vector DB globally
vdb = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding
)

# Initialize Retriever globally
retriever = vdb.as_retriever(search_kwargs={"k": 3})

def retriever_agent(state: State):
    user_input = state.get("rewritten_query")
    
    try:
        # Use the global retriever
        result = retriever.invoke(user_input)
        return {
            "context": result
        }
    except Exception as e:
        print(f"Error in retriever_agent: {e}")
        return {"context": []}

def rewrite_query_agent(state: State):
    user_input = state.get("query")
    chat_history = state.get("chat_history")

    messages = [
        SystemMessage(content=REWRITE_PROMPT),
        HumanMessage(content=query_rewrite_extend(user_input, chat_history))
    ]
    try:
        response = llm.invoke(messages)
        rewritten_query = response.content.strip()
        print(f"Rewrite Success: {rewritten_query}")
        return {
            "rewritten_query": rewritten_query
        }
    except Exception as e:
        print(f"Error in rewrite_query_agent: {e}")
        return {"rewritten_query": user_input}

def response_agent(state: State):
    user_input = state.get("rewritten_query")
    chat_history = state.get("chat_history")
    context = state.get("context")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=system_prompt_extend(user_input, str(chat_history), str(context)))
    ]
    try:
        response = llm.invoke(messages)
        final_response = response.content.strip()
        print("Response Generation Success")
        return {
            "response": final_response
        }
    except Exception as e:
        print(f"Error in response_agent: {e}")
        # Return the actual error message to the user for debugging
        return {"response": f"Sorry, I encountered an error: {str(e)}"}

        #create db
        """
Script to create Chroma vector database from Excel data
Run this once to prepare your museum data for the chatbot
"""

from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
import pandas as pd
import os

def create_database():
    print("📊 Reading Excel file...")
    
    # Read the Excel file
    try:
        df = pd.read_excel("Artifact.xlsx")
        print(f"✅ Found {len(df)} rows in the dataset")
        print(f"📋 Columns: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return
    
    # Convert DataFrame to documents
    print("\n🔄 Converting data to documents...")
    documents = []
    
    # Option 1: Combine all columns into one document per row
    for idx, row in df.iterrows():
        # Create a text representation of the row
        content_parts = []
        for col in df.columns:
            if pd.notna(row[col]):  # Skip NaN values
                content_parts.append(f"{col}: {row[col]}")
        
        content = "\n".join(content_parts)
        
        # --- Resolve Image Path for Metadata ---
        raw_image_url = str(row.get('Image_URL', ''))
        image_path = ""
        image_dir = "image for museum"
        
        if os.path.exists(image_dir) and raw_image_url and raw_image_url != 'nan':
            try:
                base_name = os.path.basename(raw_image_url)
                name_without_ext = os.path.splitext(base_name)[0].strip()
                files = os.listdir(image_dir)
                
                # Strategy A: Exact prefix match
                for f in files:
                    if f.lower().startswith(name_without_ext.lower()):
                        image_path = os.path.join(image_dir, f)
                        break
                
                # Strategy B: Remove underscores
                if not image_path:
                    name_no_under = name_without_ext.replace("_", "")
                    for f in files:
                        if f.lower().startswith(name_no_under.lower()):
                            image_path = os.path.join(image_dir, f)
                            break
            except:
                pass
                
        if not image_path and raw_image_url.startswith('http'):
            image_path = raw_image_url
            
        documents.append(Document(
            page_content=content,
            metadata={
                "row_id": idx,
                "image": image_path,
                "name_ar": str(row.get('Name_AR', '')),
                "name_en": str(row.get('Name_EN', ''))
            }
        ))
    
    print(f"✅ Created {len(documents)} documents")
    
    # Initialize embeddings
    print("\n🤖 Initializing embedding model...")
    embedding = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
    )
    print("✅ Embedding model loaded")
    
    # Create vector database
    print("\n💾 Creating Chroma vector database...")
    try:
        # Remove old database if exists
        if os.path.exists("./chroma_db"):
            import shutil
            shutil.rmtree("./chroma_db")
            print("🗑️  Removed old database")
        
        vdb = Chroma.from_documents(
            documents=documents,
            embedding=embedding,
            persist_directory="./chroma_db"
        )
        
        print("✅ Database created successfully!")
        print(f"📍 Location: ./chroma_db")
        
        # Test the database
        print("\n🧪 Testing database with a sample query...")
        retriever = vdb.as_retriever(search_kwargs={"k": 3})
        test_results = retriever.invoke("museum")
        print(f"✅ Retrieved {len(test_results)} documents")
        
        print("\n✨ All done! You can now run: streamlit run app.py")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return

if __name__ == "__main__":
    create_database()
    #models
    from typing import Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph import add_messages

class State(TypedDict):
    chat_history: Annotated[list, add_messages] # List of messages in the chat history
    #{'role': 'user', 'content': 'Hello!'}
    query: str # Current user query
    context: Optional[list[str]] # Context for the current query
    response: str # Response to the current query
    rewritten_query: str # Rewritten version of the current query
    
    #app_ui
    import streamlit as st
try:
    # Works when executed as a package module.
    from .workflow import Workflow
except ImportError:
    # Works for `streamlit run rag/app_ui.py`.
    from workflow import Workflow
from models import State
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import time
import atexit
import pandas as pd
import base64
import asyncio
from audiorecorder import audiorecorder
from groq import Groq
from artifact_names import get_artifact_keywords, correct_artifact_names_with_llm, find_closest_artifact_name
from tts_engine import generate_audio
from faq_handler import FAQSystem

# Load environment variables
load_dotenv()

# --- TTS Configuration ---
VOICE_MAPPING = {
    "ar": "ar-EG-SalmaNeural",
    "en": "en-US-JennyNeural"
}


def transcribe_audio_groq(audio_file_path, language=None, use_correction=True):
    """
    Transcribe an audio file using Groq's Whisper model with artifact name correction.
    
    Args:
        audio_file_path: Path to the audio file
        language: Language code ('ar', 'en', or None for auto-detect)
        use_correction: Whether to apply artifact name correction (default: True)
    """
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        with open(audio_file_path, "rb") as file:
            # Prepare base kwargs
            kwargs = {
                "file": (os.path.basename(audio_file_path), file.read()),
                "model": "whisper-large-v3",
                "response_format": "json",
                "temperature": 0.0
            }
            
            # Add language if specified
            if language:
                kwargs["language"] = language
                # Add prompt hint with artifact names for better accuracy
                prompt_hint = get_artifact_keywords(language)
                print(f"DEBUG: Sending prompt to Whisper (Length: {len(prompt_hint)} chars): {prompt_hint[:50]}...")
                kwargs["prompt"] = prompt_hint
                
                
            transcription = client.audio.transcriptions.create(**kwargs)
        
        transcribed_text = transcription.text
        
        # Apply correction if enabled and language is specified
        if use_correction and language and transcribed_text:
            # Try basic string matching first (faster)
            corrected_text = find_closest_artifact_name(transcribed_text, language, threshold=0.7)
            
            # If no good match found, use LLM for correction
            if corrected_text == transcribed_text:
                corrected_text = correct_artifact_names_with_llm(transcribed_text, language)
            
            return corrected_text
            
        return transcribed_text
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"


# --- 1. Configuration & State Management ---
st.set_page_config(page_title="NMEC AI Guide", layout="wide", initial_sidebar_state="collapsed")

# Initialize Session State
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'
if 'language' not in st.session_state:
    st.session_state.language = 'ar' # Default to Arabic
if 'selected_section' not in st.session_state:
    st.session_state.selected_section = None
if 'selected_item' not in st.session_state:
    st.session_state.selected_item = None
if 'selected_answer' not in st.session_state:
    st.session_state.selected_answer = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'previous_page' not in st.session_state:
    st.session_state.previous_page = 'welcome'

# --- 2. Data Loading ---
@st.cache_data
def load_museum_data():
    """Load data from CSV and structure it for the app."""
    csv_path = 'dataset_with_images.csv'
    fallback_path = 'Artifact.xlsx'
    
    data = {
        "sections": [],
        "items": {},
        "details": {}
    }
    
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        elif os.path.exists(fallback_path):
            df = pd.read_excel(fallback_path)
        else:
            st.error("Dataset not found!")
            return data

        # Process each row
        for _, row in df.iterrows():
            # Use Name_EN as ID, fallback to index if needed
            item_id = str(row.get('Name_EN', '')).strip()
            if not item_id or item_id == 'nan': 
                item_id = f"item_{_}"
            
            name_ar = row.get('Name_AR', item_id)
            if pd.isna(name_ar): name_ar = item_id
            
            name_en = row.get('Name_EN', item_id)
            if pd.isna(name_en): name_en = item_id
            
            desc_ar = row.get('Description_AR', '')
            if pd.isna(desc_ar): desc_ar = "لا يوجد وصف متاح."
            
            desc_en = row.get('Description_EN', '')
            if pd.isna(desc_en): desc_en = "No description available."

            # --- Image Handling Logic ---
            raw_image_url = str(row.get('Image_URL', ''))
            image_path = None
            
            # 1. Try to find local image in "image for museum" folder
            image_dir = "image for museum"
            if os.path.exists(image_dir) and raw_image_url and raw_image_url != 'nan':
                try:
                    base_name = os.path.basename(raw_image_url) # e.g. image.jpg
                    name_without_ext = os.path.splitext(base_name)[0] # e.g. image
                    
                    # Clean up name (remove extra spaces/newlines)
                    name_without_ext = name_without_ext.strip()
                    
                    files = os.listdir(image_dir)
                    
                    # Strategy A: Exact prefix match (case insensitive)
                    for f in files:
                        if f.lower().startswith(name_without_ext.lower()):
                            image_path = os.path.join(image_dir, f)
                            break
                    
                    # Strategy B: Remove underscores if not found
                    if not image_path:
                        name_no_under = name_without_ext.replace("_", "")
                        for f in files:
                            if f.lower().startswith(name_no_under.lower()):
                                image_path = os.path.join(image_dir, f)
                                break
                except:
                    pass

            # 2. Fallback to URL if it's a valid HTTP link
            if not image_path and raw_image_url.startswith('http'):
                image_path = raw_image_url

            # 3. Final Fallback to Placeholder
            if not image_path:
                image_path = "https://placehold.co/600x400/0E1117/C5A059?text=No+Image"
            
            image_url = image_path
            
            # Handle Hall/Section
            hall_id = str(row.get('Hall_ID', 'General')).strip()
            if pd.isna(hall_id) or hall_id == 'nan': hall_id = "General"
            
            # Create section if it doesn't exist
            if hall_id not in data["items"]:
                data["items"][hall_id] = []
                # Try to make a nice name for the section
                section_name = hall_id
                data["sections"].append({
                    "id": hall_id, 
                    "name_ar": f"قاعة {section_name}", 
                    "name_en": f"{section_name} Hall", 
                    "icon": "🏛️"
                })

            # Add to items list
            data["items"][hall_id].append({
                "id": item_id,
                "name_ar": name_ar,
                "name_en": name_en,
                "image": image_url
            })
            
            # Add to details
            data["details"][item_id] = {
                "desc_ar": desc_ar,
                "desc_en": desc_en,
                "questions": [
                    {"q_ar": "حدثني عن هذه القطعة", "q_en": "Tell me about this item"},
                    {"q_ar": "ما هو تاريخ هذه القطعة؟", "q_en": "What is the history of this item?"},
                    {"q_ar": "ما هي أهميتها؟", "q_en": "What is its significance?"}
                ]
            }
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    # Sort sections by ID to ensure consistent order (1, 2, 3, 4...)
    # Assuming IDs are numeric or sortable strings like "1", "2", "Hall 1"
    try:
        data["sections"].sort(key=lambda x: int(str(x["id"]).split()[0]) if str(x["id"]).split()[0].isdigit() else x["id"])
    except:
        data["sections"].sort(key=lambda x: x["id"])
        
    return data

MUSEUM_DATA = load_museum_data()

@st.cache_resource
def load_faq_system():
    return FAQSystem()

FAQ_SYS = load_faq_system()

def render_faq_sidebar():
    """Renders the FAQ section in the sidebar."""
    # Custom CSS for FAQ buttons and Sidebar Label
    
    st.markdown("""
    <style>
    /* Styling for FAQ Question Buttons */
    div.stButton.faq-btn > button {
        background-color: transparent;
        border: 1px solid #444;
        text-align: right;
        font-size: 0.9rem !important;
        padding: 10px;
    }
    div.stButton.faq-btn > button:hover {
        border-color: #C5A059;
        color: #C5A059;
    }
    div.stButton.faq-btn > button:focus {
        border-color: #C5A059;
        color: #C5A059;
    }
    
    /* Label for Sidebar Toggle Arrow (so user knows FAQ is there) */
    /* targeting the button explicitly to append text */
    [data-testid="stSidebarCollapsedControl"] {
        width: auto !important;
        min-width: 200px !important; /* Force width */
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        overflow: visible !important;
        background-color: transparent !important;
        border: none !important;
        z-index: 1000000 !important;
    }
    
    [data-testid="stSidebarCollapsedControl"]::after {
        content: "📋 FAQ / الأسئلة";
        color: #C5A059;
        font-weight: bold;
        padding-left: 15px;
        padding-right: 15px;
        font-size: 1rem;
        white-space: nowrap;
        visibility: visible !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        
        # Dynamic Title based on Language
        if st.session_state.language == 'ar':
            expander_title = " الأسئلة الشائعة"
        else:
            expander_title = " FAQ"
        
        with st.expander(expander_title):
            # Filter questions by current language ("Choose question language with the system")
            current_lang = st.session_state.language
            questions_list = [q for q in FAQ_SYS.search_data if q['lang'] == current_lang]
            
            if not questions_list:
                st.caption("No questions available." if current_lang == 'en' else "لا توجد أسئلة متاحة.")
            else:
                for q in questions_list:
                    # Use a unique key for each button
                    btn_key = f"faq_btn_{q['original_index']}_{q['lang']}"
                    
                    # Render button full width
                    if st.button(f"{q['question']}", key=btn_key, use_container_width=True):
                        # Show answer in a nice box immediately
                        st.success(q['answer'], icon="✅")



# --- 3. Helper Functions ---

def get_text(obj, key_prefix):
    """Retrieve text based on current language setting."""
    lang = st.session_state.language
    return obj.get(f"{key_prefix}_{lang}", obj.get(f"{key_prefix}_ar", ""))

import json
from PIL import Image, ImageOps, ImageEnhance

@st.cache_data(show_spinner=False)
def process_image(image_source, target_size=None):
    """
    Load an image, fix orientation, enhance brightness/color, and optionally resize.
    Cached to prevent re-processing on every rerun.
    """
    if isinstance(image_source, str):
        # If URL, return as is (Streamlit handles it)
        if image_source.startswith('http'):
            return image_source
            
        # Check local file existence
        if not os.path.exists(image_source):
            return "https://placehold.co/600x400?text=Image+Not+Found"

        try:
            image = Image.open(image_source)
            image = ImageOps.exif_transpose(image)
            
            # --- Enhancement ---
            # Increase Brightness
            image = ImageEnhance.Brightness(image).enhance(1.2)
            # Increase Color
            image = ImageEnhance.Color(image).enhance(1.3)
            # Increase Contrast
            image = ImageEnhance.Contrast(image).enhance(1.1)
            
            if target_size:
                image.thumbnail(target_size, Image.Resampling.LANCZOS)
                new_image = Image.new("RGBA", target_size, (0, 0, 0, 0))
                left = (target_size[0] - image.width) // 2
                top = (target_size[1] - image.height) // 2
                new_image.paste(image, (left, top))
                return new_image
                
            return image
        except Exception as e:
            print(f"Image processing error: {e}")
            return "https://placehold.co/600x400?text=Error"
            
    return image_source

def log_interaction(query, response, context, latency=0.0):
    """Log interaction to a JSONL file for later evaluation."""
    try:
        # Extract text from context documents if they are objects
        context_text = []
        if context:
            for doc in context:
                if hasattr(doc, 'page_content'):
                    context_text.append(doc.page_content)
                else:
                    context_text.append(str(doc))
        
        log_entry = {
            "query": query,
            "response": response,
            "context": "\n".join(context_text),
            "latency": latency
        }
        
        with open("session_logs.jsonl", "a", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        print(f"Failed to log interaction: {e}")

def get_ai_response(query):
    """Get response from the RAG workflow."""
    # Convert session state chat history to LangChain format
    chat_history = [HumanMessage(content=msg['content']) for msg in st.session_state.chat_history if msg['role'] != 'system']
    
    initial_state = State(
        chat_history=chat_history,
        query=query,
        context=None,
        response="",
        rewritten_query=""
    )

    try:
        start_time = time.time()
        result = Workflow().run(initial_state)
        end_time = time.time()
        latency = end_time - start_time
        
        # Log the interaction automatically
        log_interaction(
            query=query, 
            response=result.get("response", ""), 
            context=result.get("context", []),
            latency=latency
        )
        
        return result
    except Exception as e:
        return {"response": f"Error: {str(e)}", "context": []}

def navigate_to(page_name):
    """Update session state and rerun to change screen."""
    st.session_state.page = page_name
    st.rerun()

def set_background(image_file):
    """
    This function sets the background of a Streamlit app to an image specified by the given image file.
    """
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    style = f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{b64_encoded});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
    """
    st.markdown(style, unsafe_allow_html=True)

def inject_custom_css():
    """Inject CSS for styling the application."""
    
    # Determine direction based on language
    direction = "rtl" if st.session_state.language == 'ar' else "ltr"
    align = "right" if st.session_state.language == 'ar' else "left"
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

        /* Global Settings */
        .stApp {{
            direction: {direction};
            text-align: {align};
            font-family: 'Cairo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0E1117; /* Deep Charcoal / Midnight Blue */
            color: #E0E0E0; /* Off-white Text */
        }}

        /* Force text color for Markdown and other elements */
        .stMarkdown, .stText, p, div, span, li {{
            color: #E0E0E0 !important;
        }}
        
        /* Ensure st.info text is visible */
        .stAlert {{
            color: #E0E0E0 !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid #C5A059 !important;
        }}
        .stAlert p {{
            color: #E0E0E0 !important;
        }}
        
        /* Hide Streamlit Default Elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Typography */
        h1 {{
            color: #C5A059; /* Gold */
            font-size: 3rem;
            margin-bottom: 1rem;
            text-align: center;
            font-weight: 700;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.5);
        }}
        h2 {{
            color: #D4AF37; /* Metallic Gold */
            margin-top: 0;
            font-weight: 600;
            text-align: center;
        }}
        p {{
            font-size: 1.2rem;
            line-height: 1.6;
            color: #E0E0E0;
        }}

        /* Custom Button Styling (Interactive Tiles) */
        div.stButton > button {{
            width: 100%;
            height: auto;
            min-height: 120px;
            padding: 20px 40px;
            font-size: 1.5rem !important;
            font-weight: 600;
            border-radius: 10px;
            border: 1px solid #C5A059; /* Gold Border */
            background-color: rgba(255, 255, 255, 0.05); /* Semi-transparent dark grey */
            color: #E0E0E0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            margin-bottom: 15px;
            white-space: normal; /* Allow text wrap */
            line-height: 1.4;
        }}
        
        div.stButton > button:hover {{
            transform: scale(1.02); /* Subtle zoom */
            box-shadow: 0 0 15px rgba(197, 160, 89, 0.4); /* Gold glow */
            background-color: #C5A059; /* Gold Background */
            color: #0E1117; /* Dark Text */
            border: 1px solid #C5A059;
        }}
        
        div.stButton > button:active {{
            background-color: #D4AF37;
            transform: scale(0.98);
            border-color: #D4AF37;
            color: #0E1117;
        }}
        
        div.stButton > button:focus {{
            border-color: #C5A059;
            color: #E0E0E0;
            box-shadow: 0 0 0 0.2rem rgba(197, 160, 89, 0.25);
        }}

        /* Specific styling for navigation buttons (Back/Home) */
        .nav-button-container {{
            margin-top: 30px;
            border-top: 1px solid #C5A059; /* Gold separator */
            padding-top: 20px;
            opacity: 0.7;
        }}

        /* Image Styling */
        img {{
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5); /* Glow/Shadow */
            margin-bottom: 15px;
            border: 1px solid #333;
        }}
        
        /* Answer Box (Legacy class, now using st.info but keeping for custom html if needed) */
        .answer-box {{
            background-color: rgba(255, 255, 255, 0.05);
            border-right: 5px solid #C5A059; /* Gold accent */
            padding: 30px;
            border-radius: 10px;
            margin: 20px 0;
            font-size: 1.4rem;
            color: #E0E0E0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}

        /* Chat Button Styling */
        .chat-btn-container {{
            position: fixed;
            bottom: 30px;
            left: 30px; /* Default for LTR */
            z-index: 9999;
        }}
        /* Adjust for RTL */
        .stApp[data-testid="stAppViewContainer"] {{
             /* This selector is tricky in Streamlit, relying on direction set above */
        }}
        
        /* Mobile Optimization */
        @media only screen and (max-width: 600px) {{
            h1 {{
                font-size: 1.8rem !important;
                margin-bottom: 0.5rem !important;
            }}
            h2 {{
                font-size: 1.4rem !important;
            }}
            p, .stMarkdown, .stText {{
                font-size: 1rem !important;
            }}
            div.stButton > button {{
                min-height: 80px !important;
                padding: 15px 20px !important;
                font-size: 1.1rem !important;
            }}
            .chat-btn-container {{
                bottom: 15px;
                left: 15px;
            }}
        }}

    </style>
    """, unsafe_allow_html=True)

# --- 4. Screen Functions ---

def render_chat_icon():
    """Renders a small chat icon button at the top corner."""
    # Using columns to place it in the corner
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("💬", key="chat_icon", help="Chat with AI"):
            st.session_state.previous_page = st.session_state.page
            navigate_to('chat')

# --- 4. Screen Functions ---

def screen_chat():
    st.markdown("<h1>" + ("المساعد الذكي" if st.session_state.language == 'ar' else "AI Assistant") + "</h1>", unsafe_allow_html=True)
    
    # Display Chat History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display saved images if any
            if "images" in message and message["images"]:
                for img in message["images"]:
                    try:
                        st.image(process_image(img["path"]), caption=img["caption"])
                    except:
                        pass

    # Audio Recorder (Floating)
    lang = st.session_state.language
    # If AR, chat input send button is on Left, so we put Mic on Right.
    # If EN, chat input send button is on Right, so we put Mic on Left.
    # Actually, let's check Streamlit's behavior. 
    # Usually st.chat_input is centered or full width.
    # We'll place the mic in a corner to avoid overlapping the input text area too much.
    
    mic_position = "right: 10px;" if lang == 'ar' else "left: 10px;"
    
    st.markdown(f"""
    <style>
    /* Target the column containing the audio recorder iframe */
    div[data-testid="stColumn"]:has(iframe) {{
        position: fixed;
        bottom: 60px; /* Just above the bottom edge where chat input sits */
        {mic_position}
        z-index: 99999;
        width: auto !important;
        min-width: auto !important;
        flex: none !important;
        background-color: transparent;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Use a column to isolate the recorder for the CSS selector
    col_mic, col_dummy = st.columns([1, 20])
    with col_mic:
        audio = audiorecorder("🎙️", "🔴")

    # Handle Audio Input
    audio_prompt = None
    if len(audio) > 0:
        # To avoid re-processing the same audio on every rerun, we could check a hash or timestamp
        # For now, we'll rely on the user recording a new clip. 
        # A simple way is to check if this audio is different from the last processed one, 
        # but audiorecorder doesn't give a unique ID easily. 
        # We'll just process it. The user usually has to click to stop/save.
        
        # Save to temp file
        try:
            audio.export("temp_audio.wav", format="wav")
            # Transcribe
            with st.spinner("Listening..." if st.session_state.language == 'en' else "جاري الاستماع..."):
                audio_prompt = transcribe_audio_groq("temp_audio.wav", language=st.session_state.language)
        except Exception as e:
            st.error(f"Audio Error: {e}")

    # Chat Input
    text_prompt = st.chat_input("Ask something..." if st.session_state.language == 'en' else "اسأل شيئاً...")
    
    # Determine final prompt
    prompt = text_prompt if text_prompt else audio_prompt

    if prompt:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..." if st.session_state.language == 'en' else "جاري التفكير..."):
                result = get_ai_response(prompt)
                response_text = result.get("response", "Sorry, I couldn't process that request.")
                
                st.markdown(response_text)
                
                # --- Chat TTS Integration ---
                try:
                    lang = st.session_state.language
                    voice = VOICE_MAPPING.get(lang, "en-US-JennyNeural")
                    audio_path = f"chat_response_{int(time.time())}.wav"
                    
                    asyncio.run(generate_audio(
                        text=response_text,
                        voice=voice,
                        output_file=audio_path
                    ))
                    
                    # Play Audio
                    st.audio(audio_path, format="audio/wav", autoplay=True)
                    
                    # Optional: Add to file list to clean up later or keep for session
                    # For a simple approach, we leave it.
                except Exception as e:
                    print(f"Chat TTS Error: {e}")
                # ----------------------------

                # Check if user asked for images
                image_keywords = ['image', 'photo', 'picture', 'show', 'look like', 'صورة', 'صور', 'شكل', 'وريني', 'أرني']
                show_images = any(k in prompt.lower() for k in image_keywords)

                # Extract and display images from context
                context = result.get("context", [])
                images_to_show = []
                seen_paths = set()
                
                if context and show_images:
                    for doc in context:
                        # Handle both Document objects and dicts
                        metadata = doc.metadata if hasattr(doc, 'metadata') else doc.get('metadata', {})
                        image_path = metadata.get('image')
                        name = metadata.get('name_ar' if st.session_state.language == 'ar' else 'name_en', '')
                        
                        if image_path and image_path not in seen_paths:
                            # Verify file exists if it's a local path
                            if image_path.startswith('http') or os.path.exists(image_path):
                                images_to_show.append({"path": image_path, "caption": name})
                                seen_paths.add(image_path)
                                st.image(process_image(image_path), caption=name)
        
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": response_text,
            "images": images_to_show
        })
        
        # Force rerun to update chat history display and clear audio if possible
        # Note: audiorecorder might persist. 
        # We can't easily clear audiorecorder state from here without user interaction.
        # But appending to history moves the conversation forward.


    # Back Button
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if st.button("🔙 " + ("عودة" if st.session_state.language == 'ar' else "Back"), key="back_from_chat"):
        navigate_to(st.session_state.previous_page)

def screen_welcome():
    # Try to set background for welcome screen only
    bg_options = ["background.jpg", "background.png", "image for museum/Museum.png", "image for museum/Museum2.png"]
    for bg_path in bg_options:
        if os.path.exists(bg_path):
            set_background(bg_path)
            break

    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1>المتحف القومي للحضارة المصرية<br><span style='font-size: 0.7em; color: #777;'>National Museum of Egyptian Civilization</span></h1>", unsafe_allow_html=True)
    st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Arabic Button
        if st.button("العربية 🇪🇬", key="lang_ar"):
            st.session_state.language = 'ar'
            navigate_to('sections')
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # English Button
        if st.button("English 🇬🇧", key="lang_en"):
            st.session_state.language = 'en'
            navigate_to('sections')

def screen_sections():
    render_chat_icon()
    title = "اختر قسماً لاستكشافه" if st.session_state.language == 'ar' else "Choose a Section to Explore"
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    
    sections = MUSEUM_DATA['sections']
    
    # Create a grid layout (Row by Row to ensure correct order on mobile)
    for i in range(0, len(sections), 2):
        cols = st.columns(2)
        
        # First item in the row
        with cols[0]:
            section = sections[i]
            label = f"{section['icon']} {get_text(section, 'name')}"
            if st.button(label, key=f"sec_{section['id']}"):
                st.session_state.selected_section = section['id']
                navigate_to('items')
        
        # Second item in the row (if exists)
        if i + 1 < len(sections):
            with cols[1]:
                section = sections[i+1]
                label = f"{section['icon']} {get_text(section, 'name')}"
                if st.button(label, key=f"sec_{section['id']}"):
                    st.session_state.selected_section = section['id']
                    navigate_to('items')

    # Navigation Footer
    st.markdown("<div class='nav-button-container'></div>", unsafe_allow_html=True)
    col_back, col_empty = st.columns([1, 3])
    with col_back:
        back_label = "🏠 الرئيسية" if st.session_state.language == 'ar' else "🏠 Home"
        if st.button(back_label, key="back_home"):
            navigate_to('welcome')

def screen_items():
    render_chat_icon()
    sec_id = st.session_state.selected_section
    # Find section name for header
    section_info = next((s for s in MUSEUM_DATA['sections'] if s['id'] == sec_id), None)
    sec_name = get_text(section_info, 'name') if section_info else ""
    
    title = f"معروضات: {sec_name}" if st.session_state.language == 'ar' else f"Exhibits: {sec_name}"
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)

    items = MUSEUM_DATA['items'].get(sec_id, [])
    
    if not items:
        st.info("لا توجد عناصر في هذا القسم حالياً." if st.session_state.language == 'ar' else "No items in this section currently.")
    
    # Grid for items
    cols = st.columns(2)
    for idx, item in enumerate(items):
        col = cols[idx % 2]
        with col:
            # Card container
            with st.container():
                # Use a fixed target size (e.g. 800x600) to ensure consistent grid layout
                st.image(process_image(item['image'], target_size=(800, 600)), use_column_width=True)
                label = get_text(item, 'name')
                if st.button(label, key=f"item_{item['id']}"):
                    st.session_state.selected_item = item
                    navigate_to('details')

    # Navigation Footer
    st.markdown("<div class='nav-button-container'></div>", unsafe_allow_html=True)
    col_back, col_empty = st.columns([1, 3])
    with col_back:
        back_label = "🔙 العودة للأقسام" if st.session_state.language == 'ar' else "🔙 Back to Sections"
        if st.button(back_label, key="back_sections"):
            navigate_to('sections')

def screen_details():
    render_chat_icon()
    item = st.session_state.selected_item
    item_id = item['id']
    
    # Get details or default
    details = MUSEUM_DATA['details'].get(item_id, {
        "desc_ar": "عذراً، لا تتوفر معلومات تفصيلية لهذه القطعة حالياً.",
        "desc_en": "Sorry, detailed information is not available for this item currently.",
        "questions": []
    })
    
    # Layout: Image on one side (or top on mobile), Text on other
    col_img, col_info = st.columns([1, 1])
    
    with col_img:
        st.image(process_image(item['image'], target_size=(800, 600)), use_column_width=True)
    
    with col_info:
        st.markdown(f"<h2>{get_text(item, 'name')}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p>{get_text(details, 'desc')}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### " + ("اسأل عن هذه القطعة:" if st.session_state.language == 'ar' else "Ask about this item:"))
    
    questions = details.get('questions', [])
    if not questions:
        st.warning("لا توجد أسئلة متاحة." if st.session_state.language == 'ar' else "No questions available.")
    
    # Question Buttons Grid
    q_cols = st.columns(2)
    for idx, q in enumerate(questions):
        col = q_cols[idx % 2]
        with col:
            q_text = "❓ " + get_text(q, 'q')
            if st.button(q_text, key=f"q_{idx}"):
                # Use AI to answer the predefined question for better accuracy/context
                # Or fallback to hardcoded if you prefer speed. Here we use AI as requested.
                with st.spinner("Fetching answer..."):
                    # We use the question text as the query
                    query_text = get_text(q, 'q')
                    # Optionally, we could append context about the item, e.g. f"{query_text} regarding {get_text(item, 'name')}"
                    # But the RAG should handle it if the question is specific enough.
                    # Let's make it specific to be safe:
                    full_query = f"{query_text} ({get_text(item, 'name')})"
                    
                    result = get_ai_response(full_query)
                    ans = result.get("response", "Sorry, I couldn't process that request.")
                    
                    st.session_state.selected_answer = ans
                    
                    # --- TTS Integration (Pre-generate for Answer Screen) ---
                    try:
                        lang = st.session_state.language
                        voice = VOICE_MAPPING.get(lang, "en-US-JennyNeural")
                        # Run async function in sync context
                        asyncio.run(generate_audio(
                            text=ans, 
                            voice=voice,
                            output_file="response.wav"
                        ))
                    except Exception as e:
                        print(f"TTS Generation Error: {e}")
                    # ------------------------------------------------------
                    
                navigate_to('answer')

    # Navigation Footer
    st.markdown("<div class='nav-button-container'></div>", unsafe_allow_html=True)
    col_back, col_home = st.columns([1, 1])
    with col_back:
        back_label = "🔙 العودة للمعروضات" if st.session_state.language == 'ar' else "🔙 Back to Exhibits"
        if st.button(back_label, key="back_items"):
            navigate_to('items')
    
    with col_home:
        home_label = "🏠 الرئيسية" if st.session_state.language == 'ar' else "🏠 Home"
        if st.button(home_label, key="home_from_details"):
            navigate_to('welcome')
def screen_answer():
    render_chat_icon()
    st.markdown("<h1>" + ("الإجابة" if st.session_state.language == 'ar' else "The Answer") + "</h1>", unsafe_allow_html=True)
    
    # Display Answer

    # --- Play Generated Audio ---
    if os.path.exists("response.wav"):
        st.audio("response.wav", format="audio/wav")
    # ----------------------------
    # Using st.info to ensure Markdown renders correctly while keeping a "box" look
    st.info(st.session_state.selected_answer, icon="💡")
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    # Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        lbl = " سؤال آخر؟ " if st.session_state.language == 'ar' else "❓ Another Question"
        if st.button(lbl, key="ask_another"):
            navigate_to('details')
    with col2:
        lbl = "🏠 بداية جديدة" if st.session_state.language == 'ar' else "🏠 Start Over"
        if st.button(lbl, key="start_over"):
            navigate_to('welcome')

# --- 5. Main Execution Flow ---

def main():
    inject_custom_css()
    render_faq_sidebar()
    
    # Router
    if st.session_state.page == 'welcome':
        screen_welcome()
    elif st.session_state.page == 'sections':
        screen_sections()
    elif st.session_state.page == 'items':
        screen_items()
    elif st.session_state.page == 'details':
        screen_details()
    elif st.session_state.page == 'answer':
        screen_answer()
    elif st.session_state.page == 'chat':
        screen_chat()
    else:
        screen_welcome()

if __name__ == "__main__":
    main()