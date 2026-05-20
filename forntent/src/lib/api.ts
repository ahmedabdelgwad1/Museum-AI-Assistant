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
    const { data, error } = await query;
    if (error) throw error;
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
    const { data, error } = await supabase.from('museum_artifacts').select('id, content, metadata').eq('id', id).single();
    if (error) throw error;
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

export type AdminArtifactRecord = {
  id: string | number
  content?: string | null
  metadata: Record<string, any> | string | null
  created_at?: string | null
}

export async function getAdminArtifacts(page = 1, pageSize = 100) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  const res = await fetch(`${API_BASE}/artifacts/admin?${params.toString()}`, {
    cache: "no-store",
  })
  const payload = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = payload?.detail || "Failed to load admin artifacts."
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail))
  }
  return payload as { total: number; records: AdminArtifactRecord[] }
}

export async function deleteArtifact(id: string | number) {
  const res = await fetch(`${API_BASE}/artifacts/${encodeURIComponent(String(id))}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const payload = await res.json().catch(() => null)
    const detail = payload?.detail || "Failed to delete artifact."
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail))
  }
}

export type CreateArtifactInput = {
  artifact_name_en: string
  artifact_name_ar?: string
  description_en?: string
  description_ar?: string
  category_en?: string
  category_ar?: string
  hall_en?: string
  hall_ar?: string
  section_name_en?: string
  section_name_ar?: string
  section_number?: string
  image_url?: string
}

export async function createArtifact(input: CreateArtifactInput) {
  const res = await fetch(`${API_BASE}/artifacts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })

  const payload = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = payload?.detail || "Failed to save artifact."
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail))
  }
  return payload
}

export async function sendChatMessage(query: string, history: any[] = [], locale: string = "ar") {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      language: locale,
      conversation_history: history,
    }),
  })

  if (!res.ok) {
    throw new Error(`تعذر الاتصال بالسيرفر. الكود: ${res.status}`)
  }

  return await res.json()
}

export async function sendVoiceMessage(audioBlob: Blob, history: any[] = [], locale: string = "ar") {
  const formData = new FormData()
  formData.append("file", audioBlob, "recording.webm")
  formData.append("language", locale)
  formData.append("conversation_history", JSON.stringify(history))
  const res = await fetch(`${API_BASE}/voice`, {
    method: "POST",
    body: formData
  })

  if (!res.ok) {
    throw new Error(`تعذر الاتصال بالسيرفر. الكود: ${res.status}`)
  }

  return await res.json()
}
