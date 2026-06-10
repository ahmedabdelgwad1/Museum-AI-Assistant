import os
import tempfile
from pathlib import Path
from typing import Optional

# Make sure to install groq first: pip install groq
try:
    from groq import Groq
except ImportError:
    print("Please install the groq library first: pip install groq")
    exit(1)

# ==========================================
# Configuration (Replace with your API Key)
# ==========================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your-groq-api-key-here")
STT_MODEL = "whisper-large-v3"
LLM_MODEL = "llama-3.3-70b-versatile" 

# Initialize client
client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# Artifact Names Loading (From CSV)
# ==========================================
import csv
import time

_loaded_artifacts_ar = ""
_loaded_artifacts_en = ""

def load_artifacts_from_csv(csv_path: str):
    """
    Reads a CSV file and extracts Arabic and English artifact names.
    It expects columns that might be named 'artifact_name_ar' and 'artifact_name_en'
    or similar.
    """
    global _loaded_artifacts_ar, _loaded_artifacts_en
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    ar_names = set()
    en_names = set()

    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                return
                
            # Guess column names based on typical patterns
            ar_col = next((h for h in reader.fieldnames if 'ar' in h.lower() and 'name' in h.lower()), None)
            en_col = next((h for h in reader.fieldnames if 'en' in h.lower() and 'name' in h.lower()), None)
            
            # Fallback if specific columns aren't found
            if not ar_col and len(reader.fieldnames) > 0: ar_col = reader.fieldnames[0]
            if not en_col and len(reader.fieldnames) > 1: en_col = reader.fieldnames[1]

            print(f"[Info] Loading artifact names from CSV... (Found cols: AR='{ar_col}', EN='{en_col}')")
            
            for row in reader:
                if ar_col and row.get(ar_col):
                    ar_names.add(row[ar_col].strip())
                if en_col and row.get(en_col):
                    en_names.add(row[en_col].strip())

        if ar_names:
            _loaded_artifacts_ar = ", ".join(list(ar_names))
        if en_names:
            _loaded_artifacts_en = ", ".join(list(en_names))
            
        print(f"[Success] Loaded {len(ar_names)} Arabic and {len(en_names)} English artifacts from CSV.\n")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        raise

def get_artifact_keywords(language: str) -> str:
    if language == "ar":
        return _loaded_artifacts_ar
    elif language == "en":
        return _loaded_artifacts_en
    return _loaded_artifacts_ar + ", " + _loaded_artifacts_en

# ==========================================
# Transcription & Correction Logic
# ==========================================
def correct_artifact_names_with_llm(text: str, language: str) -> str:
    """
    Use an LLM to correct potentially misspelled artifact names in the transcript.
    """
    if not text.strip():
        return text
        
    print(f"  -> Applying LLM artifact name correction for {language}...")
    try:
        system_prompt = (
            "You are a spell checker for a museum transcription system. "
            "Your ONLY job is to correct misspellings of ancient Egyptian and Greco-Roman artifact names in the text. "
            "Do NOT answer the question. Do NOT add extra words. Just output the corrected text.\n"
        )
        
        system_prompt += f"Known artifact names:\n{get_artifact_keywords(language)}"
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.0,
            max_tokens=200,
        )
        
        corrected = completion.choices[0].message.content or text
        return corrected.strip()
    except Exception as exc:
        print(f"LLM STT correction failed: {exc}")
        return text


def transcribe_audio(
    audio_file_path: str,
    language: str = "ar",
    use_correction: bool = True,
) -> str:
    """
    Transcribe audio using Groq Whisper, and optionally correct artifact names.
    """
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    suffix = Path(audio_file_path).suffix.lower() or ".webm"

    try:
        kwargs = {
            "model": STT_MODEL,
            "response_format": "text",
            "temperature": 0.0,
        }

        # Language & short domain prompt
        if language == "ar":
            kwargs["language"] = "ar"
            kwargs["prompt"] = "متحف، قطعة أثرية، الصالة الإسلامية، مصرية قديمة"
        elif language == "en":
            kwargs["language"] = "en"
            kwargs["prompt"] = "museum, artifact, ancient Egyptian, Islamic"

        print(f"Transcribing {audio_file_path} using Whisper ({STT_MODEL})...")
        with open(audio_file_path, "rb") as f:
            transcription = client.audio.transcriptions.create(file=f, **kwargs)

        transcribed_text = str(transcription).strip()
        print("-" * 50)
        print("Whisper Output (Raw):")
        print(transcribed_text)
        print("-" * 50)

        # Optional LLM correction
        if use_correction and transcribed_text:
            corrected_text = correct_artifact_names_with_llm(transcribed_text, language)
            print("Output after LLM Correction:")
            print(corrected_text)
            print("-" * 50)
            return corrected_text

        return transcribed_text

    except Exception as exc:
        print(f"STT (Whisper) error: {exc}")
        raise


# ==========================================
# Execution
# ==========================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python standalone_stt_test.py <audio_file_or_folder> <path_to_csv_dataset> [language_code]")
        print("Example (Single file): python standalone_stt_test.py test.wav dataset.csv ar")
        print("Example (Folder):      python standalone_stt_test.py ./test_audios dataset.csv ar")
        sys.exit(1)
        
    target_path = sys.argv[1]
    csv_path = sys.argv[2]
    lang = sys.argv[3] if len(sys.argv) > 3 else "ar"
    
    # 1. Load context from CSV
    load_artifacts_from_csv(csv_path)
    
    # 2. Evaluate
    if os.path.isfile(target_path):
        # Single file
        transcribe_audio(target_path, language=lang, use_correction=True)
    elif os.path.isdir(target_path):
        # Batch folder evaluation
        valid_extensions = ('.wav', '.mp3', '.webm', '.ogg', '.m4a')
        files = [os.path.join(target_path, f) for f in os.listdir(target_path) if f.lower().endswith(valid_extensions)]
        
        if not files:
            print(f"No audio files found in directory: {target_path}")
            sys.exit(0)
            
        print(f"Found {len(files)} audio files in {target_path}. Starting batch evaluation...\n")
        
        for idx, file_path in enumerate(files, 1):
            print("=" * 60)
            print(f"File {idx}/{len(files)}: {os.path.basename(file_path)}")
            try:
                transcribe_audio(file_path, language=lang, use_correction=True)
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
            time.sleep(1) # Small pause between requests to avoid rate limits
        print("=" * 60)
        print("Batch evaluation completed.")
    else:
        print(f"Error: Target path '{target_path}' does not exist.")
