export interface Artifact {
  id: string;
  artifact_name_en: string;
  artifact_name_ar: string;
  description_en?: string;
  description_ar?: string;
  hall_en?: string;
  hall_ar?: string;
  image_url?: string;
  created_at?: string;
}

export interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

export interface AIResponse {
  response: string;
  language: string;
  artifact_references?: any[];
  pipeline?: string;
  rewrite_count?: number;
}
