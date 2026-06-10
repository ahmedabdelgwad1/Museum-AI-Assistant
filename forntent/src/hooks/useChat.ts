import { useState, useRef, useEffect, useMemo } from 'react';
import { ChatMessage } from '@/types';
import { getDictionary } from '@/lib/dictionaries';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Helper to parse SSE stream from FastAPI
const readSSEStream = async (
  response: Response,
  onToken: (token: string) => void,
  onDone: (audioBase64: string | null) => void,
  onError: (errorMsg: string) => void
) => {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder("utf-8");
  if (!reader) throw new Error("No reader available");

  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n\n");
    buffer = lines.pop() || ""; // keep the last incomplete chunk in the buffer

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const jsonStr = line.slice(6);
        try {
          const data = JSON.parse(jsonStr);
          if (data.type === "token") {
            onToken(data.content);
          } else if (data.type === "done") {
            onDone(data.audio_base64 || null);
          } else if (data.type === "error") {
            onError(data.content);
          }
        } catch (e) {
          console.error("Error parsing SSE JSON:", e, jsonStr);
        }
      }
    }
  }
};

export function useChat(artifact: any, locale: 'en' | 'ar') {
  const dict = useMemo(() => getDictionary(locale), [locale]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { 
      role: 'ai', 
      content: locale === 'en' 
        ? `Tell me about ${artifact?.artifact_name_en || 'this artifact'}` 
        : `حدثني عن ${artifact?.artifact_name_ar || 'هذه القطعة'}` 
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const stopCurrentAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopCurrentAudio();
  }, []);

  const startRecording = async () => {
    stopCurrentAudio();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        sendAudioToFastAPI(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert(locale === 'ar' ? 'حدث خطأ أثناء الوصول للمايكروفون. تأكد من إعطاء الصلاحيات.' : 'Error accessing microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const streamChatResponse = async (query: string, historyToSend: any[]) => {
    // Add Thinking AI message to be replaced via streaming
    setMessages(prev => [...prev, { role: 'ai', content: dict.ai.thinking }]);
    
    let isFirstToken = true;

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, language: locale, conversation_history: historyToSend })
      });

      if (!response.ok) throw new Error('Network response was not ok');

      await readSSEStream(
        response,
        (token) => {
          setMessages(prev => {
            const newMsgs = [...prev];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg.role === 'ai') {
              // Replace "Thinking..." with the first token, then append subsequent tokens
              const currentContent = isFirstToken ? '' : lastMsg.content;
              isFirstToken = false;
              newMsgs[newMsgs.length - 1] = {
                ...lastMsg,
                content: currentContent + token
              };
            }
            return newMsgs;
          });
        },
        (audioBase64) => {
          if (audioBase64) {
            stopCurrentAudio();
            const audioUrl = `data:audio/mp3;base64,${audioBase64}`;
            const audio = new Audio(audioUrl);
            currentAudioRef.current = audio;
            audio.play();
          }
        },
        (errorMsg) => {
          setMessages(prev => {
            const newMsgs = [...prev];
            newMsgs[newMsgs.length - 1] = { role: 'ai', content: `[Error] ${errorMsg}` };
            return newMsgs;
          });
        }
      );
    } catch (error) {
      console.error("Streaming error:", error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { role: 'ai', content: locale === 'ar' ? 'حدث خطأ في الاتصال بالخادم.' : 'Error connecting to the server.' };
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const sendAudioToFastAPI = async (audioBlob: Blob) => {
    setMessages(prev => [...prev, { role: 'user', content: locale === 'ar' ? '🎤 جاري الاستماع...' : '🎤 Listening...' }]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "audio.webm");
      formData.append("language", locale);

      // Step 1: Transcribe fast
      const response = await fetch(`${API_URL}/transcribe`, { 
        method: "POST", 
        body: formData 
      });

      if (!response.ok) throw new Error("Transcription failed");
      
      const data = await response.json();
      const transcript = data.transcript;

      // Replace "Listening..." with actual transcript
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { role: 'user', content: transcript };
        return newMsgs;
      });

      // Prepare history (excluding the current voice message since we pass it as query)
      const historyToSend = messages
        .filter(m => m.content && !m.content.includes('🎤'))
        .map(m => ({ role: m.role, content: m.content }));

      // Step 2: Stream LLM response
      await streamChatResponse(transcript, historyToSend);

    } catch (error: any) {
      console.error("Error sending voice:", error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { role: 'ai', content: locale === 'ar' ? 'حدث خطأ في معالجة الصوت.' : 'Error processing voice.' };
        return newMsgs;
      });
      setIsLoading(false);
    }
  };

  const sendMessage = async (msg: string) => {
    stopCurrentAudio();
    if (!msg.trim() || isLoading) return;
    
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setInput('');
    setIsLoading(true);

    const historyToSend = messages
      .filter(m => m.content && !m.content.includes('🎤'))
      .map(m => ({ role: m.role, content: m.content }));

    await streamChatResponse(msg, historyToSend);
  };

  return {
    messages,
    input,
    setInput,
    sendMessage,
    isLoading,
    isRecording,
    startRecording,
    stopRecording,
    dict,
    dir: locale === 'ar' ? 'rtl' : 'ltr'
  };
}
