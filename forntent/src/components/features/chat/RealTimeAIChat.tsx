"use client";
import { Send, Mic, Sparkles } from "lucide-react";
import { useChat } from "@/hooks/useChat";

type Props = {
  artifact?: any;
  locale: "en" | "ar";
  embedded?: boolean;
};

export function RealTimeAIChat({ artifact, locale, embedded = false }: Props) {
  const { messages, input, setInput, sendMessage, dict, dir, isLoading, isRecording, startRecording, stopRecording } = useChat(artifact, locale);
  const isAr = locale === "ar";

  const send = (msg: string) => {
    sendMessage(msg);
  };

  return (
    <div className={`flex flex-col ${embedded ? 'h-full w-full' : 'h-[600px] md:h-[calc(100vh)] border-l border-border sticky top-0'} bg-bg-card`} dir={dir}>
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

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {messages.map((m, i) => (
          <div key={i} className={`p-3 rounded-lg max-w-[80%] ${
            m.role === 'user'
              ? 'bg-gold text-bg-primary self-end'
              : `bg-bg-primary ${isAr ? 'border-r-4' : 'border-l-4'} border-gold self-start text-text-primary`
          }`}>
            {m.role === 'ai' && <div className="text-[10px] opacity-70 mb-1">{dict.ai?.senderName || 'Museum Guide'} 🤖</div>}
            <p className={`text-sm ${isAr ? 'font-(family-name:--font-almarai)' : 'font-sans'}`}>{m.content}</p>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-border bg-bg-primary">
        <div className="flex items-center gap-2">
          <button 
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
            className={`p-2 rounded-full transition-colors ${
              isRecording 
                ? "bg-red-500 text-white animate-pulse" 
                : "bg-bg-card text-text-secondary hover:text-gold"
            }`}
            title={isAr ? "اضغط باستمرار للتسجيل" : "Hold to record"}
          >
            <Mic className="w-5 h-5" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send(input)}
            placeholder={isRecording ? (isAr ? 'جاري التسجيل...' : 'Recording...') : (dict.detail?.inputPlaceholder || (isAr ? 'رسالتك...' : 'Message...'))}
            className="flex-1 bg-bg-card border border-border rounded-full px-4 py-2 text-sm focus:outline-none focus:border-gold text-text-primary"
            disabled={isLoading || isRecording}
          />
          <button onClick={() => send(input)} disabled={isLoading || isRecording} className="p-2 rounded-full bg-gold text-bg-primary disabled:opacity-50">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
