import { AIResponse } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChatMessage(
  query: string,
  language: 'en' | 'ar',
  conversationHistory: Array<{ role: string; content: string }> = []
): Promise<AIResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      language,
      conversation_history: conversationHistory,
    }),
  });
  if (!response.ok) throw new Error('Failed to fetch AI response');
  return await response.json();
}
