import sys
import asyncio
from PIL import Image
import os
import json

# Setup sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.dinov2 import DinoV2Encoder
from app.rag.vectorstore import get_supabase_client

def main(image_path: str):
    print(f"Loading image from {image_path}...")
    try:
        pil_img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Failed to load image: {e}")
        return

    print("Initializing DINOv2 model (this may take a moment to download weights if first time)...")
    encoder = DinoV2Encoder.get_instance()
    
    print("Generating 768-dim visual embedding...")
    visual_vec = encoder.embed(pil_img)
    
    if not visual_vec:
        print("Failed to generate embedding.")
        return
        
    print("Querying Supabase for matching artifacts...")
    try:
        client = get_supabase_client()
        response = client.rpc(
            "match_visual_artifacts",
            {
                "query_embedding": visual_vec,
                "match_threshold": 0.40, # Allow a bit higher distance for testing
                "match_count": 3
            }
        ).execute()
        
        if response.data:
            print("\n✅ Match Found!")
            for i, match in enumerate(response.data):
                meta = match.get("metadata", {})
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except:
                        pass
                
                name_ar = meta.get('artifact_name_ar', 'غير معروف')
                name_en = meta.get('artifact_name_en', 'Unknown')
                distance = match.get("dist", match.get("distance", 0.0))
                similarity = 1.0 - distance
                print(f"[{i+1}] {name_ar} ({name_en}) - Similarity: {similarity:.2f} (Distance: {distance:.2f})")
        else:
            print("\n❌ No match found above the threshold. This means the model saw the picture but didn't find a close enough vector in the database.")
    except Exception as e:
        print(f"Database query failed: {e}")
        print("Did you remember to run the SQL migration from DATABASE_SCHEMA_FOR_AI.md?")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_vision.py <path_to_image>")
        sys.exit(1)
        
    main(sys.argv[1])
