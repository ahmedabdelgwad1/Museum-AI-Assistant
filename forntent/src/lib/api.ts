const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function getArtifacts(sectionId?: number, search?: string) {
  const params = new URLSearchParams()
  if (sectionId) params.append("section", sectionId.toString())
  if (search) params.append("q", search)
  try {
    const res = await fetch(`${API_BASE}/artifacts?${params}`)
    return await res.json()
  } catch (e) {
    return []
  }
}

export async function getArtifact(id: string) {
  try {
    const res = await fetch(`${API_BASE}/artifacts/${id}`)
    return await res.json()
  } catch(e) {
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
