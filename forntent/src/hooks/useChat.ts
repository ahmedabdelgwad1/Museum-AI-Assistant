import { useState, useRef } from 'react';
import { ChatMessage, AIResponse } from '@/types';
import { getDictionary } from '@/lib/dictionaries';

export function useChat(artifact: any, locale: 'en' | 'ar') {
  const dict = getDictionary(locale);
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

  const startRecording = async () => {
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
        // Stop all audio tracks to release the microphone
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

  const sendAudioToFastAPI = async (audioBlob: Blob) => {
    // Show user a message indicating audio is being processed
    setMessages(prev => [...prev, { role: 'user', content: locale === 'ar' ? '🎤 رسالة صوتية...' : '🎤 Voice message...' }]);
    setIsLoading(true);

    // Placeholder: This is where you will send the `audioBlob` to your FastAPI server
    // const formData = new FormData();
    // formData.append("file", audioBlob, "audio.webm");
    // const response = await fetch("http://YOUR_FASTAPI_URL/transcribe_and_chat", { method: "POST", body: formData });
    
    // Simulating backend delay for Whisper + LLM
    setTimeout(() => {
      setMessages(prev => [...prev, { role: 'ai', content: dict.ai.thinking }]);
      setTimeout(() => {
        setMessages(prev => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1] = { 
            role: 'ai', 
            content: locale === 'en' 
              ? "[Audio Processed by Whisper] This is a simulated response based on your audio." 
              : "[تم معالجة الصوت بـ Whisper] هذا رد تجريبي بناءً على رسالتك الصوتية." 
          };
          return newMsgs;
        });
        setIsLoading(false);
      }, 1000);
    }, 1500);
  };

  const sendMessage = async (msg: string) => {
    if (!msg.trim() || isLoading) return;
    
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setInput('');
    setIsLoading(true);

    // Placeholder simulated response, to be connected to FastAPI later
    setTimeout(() => {
      setMessages(prev => [...prev, { role: 'ai', content: dict.ai.thinking }]);
      setTimeout(() => {
        setMessages(prev => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1] = { 
            role: 'ai', 
            content: locale === 'en' 
              ? "This is a placeholder response from Alex. I can provide historical context and details." 
              : "هذا رد تجريبي من إسكندر. يمكنني تزويدك بمعلومات تاريخية وتفاصيل أثرية." 
          };
          return newMsgs;
        });
        setIsLoading(false);
      }, 1000);
    }, 500);
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
