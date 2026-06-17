import { createClient } from "@supabase/supabase-js"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || ""
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""

// A generic client safe for both Server and Client components (for public data)
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// Supabase Storage bucket name for artifact images
const IMAGE_BUCKET = "artifact-images"

export async function uploadImage(file: File): Promise<string> {
  const ext = file.name.split(".").pop() || "jpg"
  const fileName = `${Date.now()}-${Math.random().toString(36).slice(2)}.${ext}`

  const { error } = await supabase.storage
    .from(IMAGE_BUCKET)
    .upload(fileName, file, { upsert: false, contentType: file.type })

  if (error) throw new Error(error.message)

  const { data } = supabase.storage.from(IMAGE_BUCKET).getPublicUrl(fileName)
  return data.publicUrl
}

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
  const from = (page - 1) * pageSize
  const to = from + pageSize - 1
  
  const result = await supabase
    .from("museum_artifacts")
    .select("id, metadata", { count: "exact" })
    .order("id", { ascending: true })
    .range(from, to)

  if (result.error) throw result.error

  // Map the relational data back to the format the Admin UI expects
  const mappedRecords = (result.data || []).map(row => {
    const meta = typeof row.metadata === 'string' ? JSON.parse(row.metadata) : (row.metadata || {});
    return {
      id: row.id,
      metadata: meta,
      // Since created_at might not exist in the vectorstore, we just use a fallback or omit
      created_at: new Date().toISOString() // Temporary fallback for recent activity sorting
    }
  }) as AdminArtifactRecord[];

  return {
    total: result.count || 0,
    records: mappedRecords,
  }
}

export async function deleteArtifact(id: string | number, imageUrl?: string) {
  // 1. Delete from backend DB (backend now handles image deletion securely via service_role)
  const res = await fetch(`${API_BASE}/artifacts/${encodeURIComponent(String(id))}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const payload = await res.json().catch(() => null)
    const detail = payload?.detail || "Failed to delete artifact."
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail))
  }
}

export type UpdateArtifactInput = {
  artifact_name_en?: string
  artifact_name_ar?: string
  description_en?: string
  description_ar?: string
  section_name_en?: string
  section_name_ar?: string
  image_url?: string
}

export async function updateArtifact(id: string | number, input: UpdateArtifactInput) {
  const res = await fetch(`${API_BASE}/artifacts/${encodeURIComponent(String(id))}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })
  const payload = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = payload?.detail || "Failed to update artifact."
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail))
  }
  return payload
}
export async function translateBatch(fields_to_translate: { field_id: string, source_text: string, target_lang: "ar" | "en" }[]) {
  if (fields_to_translate.length === 0) return {};
  
  const res = await fetch(`${API_BASE}/artifacts/translate-batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fields_to_translate }),
  });
  if (!res.ok) throw new Error("Batch translation failed");
  const data = await res.json();
  return data.translations as Record<string, string>;
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

export async function translateText(text: string, target_lang: "ar" | "en"): Promise<string> {
  const res = await fetch(`${API_BASE}/artifacts/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, target_lang }),
  })
  
  if (!res.ok) {
    throw new Error("Translation failed")
  }
  const payload = await res.json()
  return payload.translated_text || ""
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
