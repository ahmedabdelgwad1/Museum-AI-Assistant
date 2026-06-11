/**
 * Drop-in replacement for the legacy chat hook using LiveKit WebRTC.
 *
 * Returns the same shape as the old chat hook:
 *   { messages, input, setInput, sendMessage, isLoading,
 *     isRecording, startRecording, stopRecording, dict, dir }
 *
 * Key differences from the legacy hook:
 *   - No browser-side audio blob packaging
 *   - No legacy REST streaming or transcription calls
 *   - Audio is a continuous WebRTC track managed by LiveKit
 *   - VAD and interruptions are handled server-side by the Agent
 */
import { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import {
  Room,
  RoomEvent,
  type Participant,
} from 'livekit-client';
import { ChatMessage } from '@/types';
import { getDictionary } from '@/lib/dictionaries';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const LIVEKIT_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL || '';
const CHAT_TOPIC = 'lk.chat';

export function useLiveKit(artifact: any, locale: 'en' | 'ar') {
  const dict = useMemo(() => getDictionary(locale), [locale]);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'ai',
      content:
        locale === 'en'
          ? `Tell me about ${artifact?.artifact_name_en || 'this artifact'}`
          : `حدثني عن ${artifact?.artifact_name_ar || 'هذه القطعة'}`,
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const roomRef = useRef<Room | null>(null);

  const appendTranscript = useCallback((role: ChatMessage['role'], content: string) => {
    const text = content.trim();
    if (!text) return;

    setMessages(prev => {
      const last = prev[prev.length - 1];
      if (last?.role === role && last.content.trim() === text) {
        return prev;
      }

      return [...prev, { role, content: text }];
    });
  }, []);

  // ------------------------------------------------------------------
  // Connect to LiveKit room
  // ------------------------------------------------------------------
  const connect = useCallback(async (enableMicrophone = false) => {
    try {
      if (!LIVEKIT_URL) {
        throw new Error('NEXT_PUBLIC_LIVEKIT_URL is not configured');
      }

      if (roomRef.current && isConnected) {
        if (enableMicrophone) {
          await roomRef.current.localParticipant.setMicrophoneEnabled(true);
          setIsRecording(true);
        }
        return roomRef.current;
      }

      setIsConnecting(true);

      const res = await fetch(`${API_URL}/livekit/token?visitor_id=user&locale=${locale}`);
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to fetch LiveKit token: ${res.status} ${res.statusText} - ${errorText}`);
      }
      const { token } = await res.json();

      const room = new Room();
      roomRef.current = room;

      room.on(RoomEvent.TranscriptionReceived, (segments, participant?: Participant) => {
        const finalText = segments
          .filter(segment => segment.final)
          .map(segment => segment.text)
          .join(' ')
          .trim();

        if (!finalText) return;

        const role = participant?.identity === room.localParticipant.identity ? 'user' : 'ai';
        appendTranscript(role, finalText);

        if (role === 'user') {
          setIsLoading(true);
        } else {
          setIsLoading(false);
        }
      });

      room.on(RoomEvent.Connected, () => {
        setIsConnected(true);
      });

      // CRITICAL: Attach the agent's audio track to the DOM so it actually plays!
      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        if (track.kind === 'audio') {
          const audioElement = track.attach();
          // Optional: Add to DOM if needed, but attach() usually plays it automatically 
          // if it's an audio track, though appending ensures it doesn't get garbage collected.
          document.body.appendChild(audioElement);
        }
      });
      
      room.on(RoomEvent.TrackUnsubscribed, (track) => {
        track.detach();
      });

      room.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setIsRecording(false);
      });

      await room.connect(LIVEKIT_URL, token);
      setIsConnected(true);
      setIsConnecting(false);

      if (enableMicrophone) {
        // Enable microphone — LiveKit handles VAD and streaming from here
        await room.localParticipant.setMicrophoneEnabled(true);
        setIsRecording(true);
      }

      return room;
    } catch (err) {
      console.error('LiveKit connection error:', err);
      setIsLoading(false);
      setIsRecording(false);
      setIsConnected(false);
      setIsConnecting(false);
      roomRef.current = null;
      throw err;
    }
  }, [appendTranscript, isConnected]);

  // ------------------------------------------------------------------
  // Disconnect
  // ------------------------------------------------------------------
  const disconnect = useCallback(async () => {
    setIsRecording(false);
    setIsConnected(false);
    setIsConnecting(false);
    if (roomRef.current) {
      await roomRef.current.localParticipant.setMicrophoneEnabled(false);
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // ------------------------------------------------------------------
  // startRecording / stopRecording — same API surface as the old hook
  // ------------------------------------------------------------------
  const startRecording = useCallback(async () => {
    if (!isConnected) {
      await connect(true);
    } else if (roomRef.current) {
      await roomRef.current.localParticipant.setMicrophoneEnabled(true);
      setIsRecording(true);
    }
  }, [isConnected, connect]);

  const stopRecording = useCallback(async () => {
    await disconnect();
  }, [disconnect]);

  // ------------------------------------------------------------------
  // sendMessage — text input path (unchanged UX, sends via data channel)
  // ------------------------------------------------------------------
  const sendMessage = useCallback(
    async (msg: string) => {
      if (!msg.trim() || isLoading) return;

      setMessages(prev => [...prev, { role: 'user', content: msg }]);
      setInput('');
      setIsLoading(true);

      try {
        const room = roomRef.current && isConnected ? roomRef.current : await connect(false);
        await room.localParticipant.sendText(msg, { topic: CHAT_TOPIC });
      } catch (err) {
        console.error('LiveKit text message error:', err);
        setIsLoading(false);
      }
    },
    [isLoading, isConnected, connect]
  );

  return {
    messages,
    input,
    setInput,
    sendMessage,
    isLoading,
    isRecording,
    isConnecting,
    startRecording,
    stopRecording,
    dict,
    dir: locale === 'ar' ? 'rtl' : 'ltr',
    isConnected,
    room: roomRef.current,
  };
}
