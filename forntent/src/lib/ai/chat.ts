import { AIResponse } from '@/types';

export async function sendChatMessage(query: string, language: 'en' | 'ar'): Promise<AIResponse> {
  // Placeholder for FastAPI integration
  // const response = await fetch(`${process.env.NEXT_PUBLIC_AI_API_URL}/chat`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ query, language }),
  // });
  // if (!response.ok) throw new Error('Failed to fetch AI response');
  // return await response.json();
  
  return {
    response: "This is a placeholder response from the AI backend.",
    language,
    pipeline: "corrective_rag"
  };
}
