from app.rag.vectorstore import get_supabase_client, get_by_id
from urllib.parse import urlparse

def delete_image_for_artifact(artifact_id: str):
    client = get_supabase_client()
    artifact = get_by_id(artifact_id)
    if not artifact:
        print("Artifact not found")
        return
        
    metadata = artifact.get("metadata", {})
    image_url = metadata.get("image_url")
    if image_url and "artifact-images" in image_url:
        path = urlparse(image_url).path
        filename = path.split("/")[-1]
        print(f"Deleting image {filename} from bucket artifact-images")
        client.storage.from_("artifact-images").remove([filename])
        print("Done")
    else:
        print("No image or not in our bucket")

# Let's not actually delete anything right now, just verify parsing
delete_image_for_artifact("96")
