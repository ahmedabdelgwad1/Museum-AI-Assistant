import { useState, useRef, useEffect } from 'react';
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
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const stopCurrentAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
  };

  // Stop audio if the user leaves the page
  useEffect(() => {
    return () => {
      stopCurrentAudio();
    };
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
    setMessages(prev => [...prev, { role: 'user', content: locale === 'ar' ? '🎤 رسالة صوتية...' : '🎤 Voice message...' }]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "audio.webm");

      const historyToSend = messages
        .filter(m => m.content !== dict.ai.thinking && !m.content.includes('رسالة صوتية') && !m.content.includes('Voice message'))
        .map(m => ({ role: m.role, content: m.content }));
      formData.append("conversation_history", JSON.stringify(historyToSend));
      
      setMessages(prev => [...prev, { role: 'ai', content: dict.ai.thinking }]);

      const API_URL = "https://ahmed3182004-museum-backend.hf.space";
      const response = await fetch(`${API_URL}/voice`, { 
        method: "POST", 
        body: formData 
      });

      if (!response.ok) {
        let errorDetail = "Failed to process voice query";
        try {
          const errBody = await response.json();
          if (errBody.detail) errorDetail = errBody.detail;
        } catch (e) {}
        throw new Error(errorDetail);
      }

      const data = await response.json();
      
      if (data.audio_base64) {
        stopCurrentAudio();
        const audioUrl = `data:audio/mp3;base64,${data.audio_base64}`;
        const audio = new Audio(audioUrl);
        currentAudioRef.current = audio;
        audio.play();
      }

      setMessages(prev => {
        const newMsgs = [...prev];
        // Remove the "Thinking..." message
        newMsgs.pop(); 
        // Remove the "Voice message..." message
        newMsgs.pop(); 

        // Add the actual transcript as a user message
        newMsgs.push({ role: 'user', content: data.transcript });
        // Add the AI response text
        newMsgs.push({ role: 'ai', content: data.response });
        
        return newMsgs;
      });
    } catch (error: any) {
      console.error("Error sending voice:", error);
      setMessages(prev => {
        const newMsgs = [...prev];
        const errorMessage = error.message || (locale === 'ar' ? 'حدث خطأ في معالجة الصوت.' : 'Error processing voice.');
        newMsgs[newMsgs.length - 1] = { role: 'ai', content: `[Error] ${errorMessage}` };
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (msg: string) => {
    stopCurrentAudio();
    if (!msg.trim() || isLoading) return;
    
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setInput('');
    setIsLoading(true);

    setMessages(prev => [...prev, { role: 'ai', content: dict.ai.thinking }]);

    try {
      const historyToSend = messages
        .filter(m => m.content !== dict.ai.thinking && !m.content.includes('رسالة صوتية') && !m.content.includes('Voice message'))
        .map(m => ({ role: m.role, content: m.content }));

      const API_URL = "https://ahmed3182004-museum-backend.hf.space";
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: msg,
          language: locale,
          conversation_history: historyToSend
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { 
          role: 'ai', 
          content: data.response || "No response received" 
        };
        return newMsgs;
      });

      // If the backend returns audio_base64, play it
      if (data.audio_base64) {
        stopCurrentAudio(); // Strictly stop any audio that might have started during the loading time
        const audioUrl = `data:audio/mp3;base64,${data.audio_base64}`;
        const audio = new Audio(audioUrl);
        currentAudioRef.current = audio;
        audio.play();
      }

    } catch (error) {
      console.error("Error fetching chat:", error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { 
          role: 'ai', 
          content: locale === 'ar' ? 'حدث خطأ في الاتصال بالخادم.' : 'Error connecting to the server.' 
        };
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
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
