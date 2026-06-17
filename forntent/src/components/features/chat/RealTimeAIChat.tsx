"use client";
import { Send, Mic, Sparkles, Eye, User } from "lucide-react";
import { useLiveKit as useChat } from "@/hooks/useLiveKit";
import { RoomAudioRenderer } from "@livekit/components-react";

type Props = {
  artifact?: any;
  locale: "en" | "ar";
  embedded?: boolean;
};

export function RealTimeAIChat({ artifact, locale, embedded = false }: Props) {
  const { messages, input, setInput, sendMessage, dict, dir, isLoading, isRecording, isConnecting, startRecording, stopRecording, room } = useChat(artifact, locale);
  const isAr = locale === "ar";

  const send = (msg: string) => {
    sendMessage(msg);
  };

  return (
    <div className={`flex flex-col ${embedded ? 'h-full w-full' : 'h-[600px] md:h-[calc(100vh)] border-l border-border sticky top-0'} bg-bg-card`} dir={dir}>
      {room && <RoomAudioRenderer room={room} />}
      {!embedded && (
        <>
          <div className="p-4 border-b border-border flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-gold" />
            <h2 className={`font-bold text-gold ${isAr ? 'font-(family-name:--font-almarai) text-xl' : 'font-(family-name:--font-inter)'}`}>
              {dict.detail?.askAbout || (isAr ? 'اسأل عن القطعة' : 'Ask about artifact')}
            </h2>
          </div>

          <div className="p-4 border-b border-border bg-bg-primary overflow-x-auto whitespace-nowrap flex gap-2" style={{ scrollbarWidth: 'none' }}>
            <span className="text-xs text-text-secondary self-center mr-2">{dict.detail?.quickQuestions || (isAr ? 'أسئلة سريعة' : 'Quick questions')}</span>
            {[dict.detail?.q1, dict.detail?.q2, dict.detail?.q3].filter(Boolean).map((q, i) => (
              <button 
                key={i} 
                onClick={() => send(q as string)}
                disabled={isLoading || isRecording}
                className="inline-block px-3 py-1 bg-bg-card border border-border rounded-full text-xs hover:border-gold transition-colors text-text-primary disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        </>
      )}

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-6">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-text-secondary opacity-50 gap-3">
            <div className="w-16 h-16 rounded-full bg-gold/5 flex items-center justify-center border border-gold/20 shadow-[0_0_15px_rgba(212,175,55,0.1)]">
              <Eye className="w-8 h-8 text-gold drop-shadow-md" />
            </div>
            <p className={`text-sm ${isAr ? 'font-(family-name:--font-almarai)' : ''}`}>{isAr ? 'المرشد الذكي جاهز للإجابة...' : 'Smart Guide is ready to answer...'}</p>
          </div>
        ) : (
          messages.map((m, i) => {
            const isUser = m.role === 'user';
            return (
              <div key={i} className={`flex w-full gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 transition-all ${isUser ? 'bg-bg-card border border-border text-text-secondary' : 'bg-gold/10 border border-gold/50 text-gold shadow-[0_0_10px_rgba(212,175,55,0.15)]'}`}>
                  {isUser ? <User className="w-4 h-4" /> : <Eye className="w-5 h-5 drop-shadow-md" />}
                </div>

                {/* Message Bubble */}
                <div className={`p-3 rounded-2xl max-w-[80%] ${
                  isUser
                    ? `bg-gold text-bg-primary shadow-md ${isAr ? 'rounded-tl-none' : 'rounded-tr-none'}`
                    : `bg-bg-card border border-border text-text-primary shadow-sm ${isAr ? 'rounded-tr-none' : 'rounded-tl-none'}`
                }`}>
                  {!isUser && <div className="text-[10px] opacity-80 mb-1.5 font-bold text-gold tracking-widest uppercase flex items-center gap-1">
                    {dict.ai?.senderName || (isAr ? 'المرشد الذكي' : 'MUSEUM GUIDE')}
                  </div>}
                  <p className={`text-sm leading-relaxed ${isAr ? 'font-(family-name:--font-almarai)' : 'font-sans'}`}>{m.content}</p>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="p-4 border-t border-border bg-bg-primary">
        <div className="flex items-center gap-2">
          <button 
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isConnecting}
            className={`p-2 rounded-full transition-colors ${
              isConnecting
                ? "bg-yellow-500 text-white animate-pulse"
                : isRecording 
                  ? "bg-red-500 text-white animate-pulse" 
                  : "bg-bg-card text-text-secondary hover:text-gold"
            }`}
            title={isConnecting ? (isAr ? "جاري الاتصال..." : "Connecting...") : isAr ? (isRecording ? "إيقاف المكالمة" : "بدء المكالمة") : (isRecording ? "End Call" : "Start Call")}
          >
            <Mic className="w-5 h-5" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send(input)}
            placeholder={isConnecting ? (isAr ? 'جاري الاتصال...' : 'Connecting...') : isRecording ? (isAr ? 'تحدث الآن، أنا أستمع...' : 'Speak now, listening...') : (dict.detail?.inputPlaceholder || (isAr ? 'رسالتك...' : 'Message...'))}
            className="flex-1 bg-bg-card border border-border rounded-full px-4 py-2 text-sm focus:outline-none focus:border-gold text-text-primary"
            disabled={isLoading || isRecording || isConnecting}
          />
          <button onClick={() => send(input)} disabled={isLoading || isRecording || isConnecting} className="p-2 rounded-full bg-gold text-bg-primary disabled:opacity-50">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
