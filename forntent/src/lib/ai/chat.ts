import { AIResponse } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://ahmed3182004-museum-backend.hf.space";

export async function sendChatMessage(query: string, language: 'en' | 'ar'): Promise<AIResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, language }),
  });
  if (!response.ok) throw new Error('Failed to fetch AI response');
  return await response.json();
}
