import { createClient } from "@supabase/supabase-js"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || ""
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""

// A generic client safe for both Server and Client components (for public data)
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

export async function getArtifacts(sectionId?: number, search?: string) {
  try {
    let query = supabase.from('museum_artifacts').select('id, metadata');
    
    // Supabase jsonb filtering requires specific syntax, but for simplicity
    // we'll fetch all and filter in JS if it's not a massive DB. 
    // Since we have 96 rows, this is extremely fast.
    const { data } = await query;
    if (!data) return [];
    
    let results = data.map(row => {
      const meta = typeof row.metadata === 'string' ? JSON.parse(row.metadata) : row.metadata;
      return {
        id: row.id,
        ...meta
      };
    });

    if (sectionId) {
      results = results.filter(item => item.section_number == sectionId);
    }
    
    if (search) {
      const s = search.toLowerCase();
      results = results.filter(item => 
        (item.artifact_name_en && item.artifact_name_en.toLowerCase().includes(s)) ||
        (item.artifact_name_ar && item.artifact_name_ar.includes(s))
      );
    }

    return results;
  } catch (e) {
    console.error("Error fetching artifacts:", e);
    return []
  }
}

export async function getArtifact(id: string) {
  try {
    const { data } = await supabase.from('museum_artifacts').select('id, content, metadata').eq('id', id).single();
    if (!data) return null;
    
    const meta = typeof data.metadata === 'string' ? JSON.parse(data.metadata) : data.metadata;
    return {
      id: data.id,
      content: data.content,
      ...meta
    };
  } catch(e) {
    console.error("Error fetching artifact:", e);
    return null;
  }
}

export async function sendChatMessage(query: string, artifactContext?: object) {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, artifact_context: artifactContext })
    })
    return await res.json()
  } catch (e) {
    return { response: "Failed to connect to AI server." }
  }
}

export async function sendVoiceMessage(audioBlob: Blob) {
  const formData = new FormData()
  formData.append("audio", audioBlob, "recording.webm")
  const res = await fetch(`${API_BASE}/voice`, {
    method: "POST",
    body: formData
  })
  return res.blob() // returns MP3
}
