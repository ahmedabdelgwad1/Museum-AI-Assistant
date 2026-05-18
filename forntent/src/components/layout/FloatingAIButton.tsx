"use client";
import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X, Send, Mic } from "lucide-react";
import { getDictionary, hFont, dir } from "@/lib/dictionaries";
import { useChat } from "@/hooks/useChat";

export function FloatingAIButton({ locale }: { locale: "en" | "ar" }) {
  const [isOpen, setIsOpen] = useState(false);
  
  // Use the real backend hook instead of mock messages
  const { 
    messages, 
    input, 
    setInput, 
    sendMessage, 
    isLoading, 
    isRecording, 
    startRecording, 
    stopRecording 
  } = useChat(null, locale);

  const dict = getDictionary(locale);
  const isAr = locale === "ar";
  const d = dir(locale);

  // We can just use sendMessage directly
  const send = (msg: string) => {
    sendMessage(msg);
  };

  return (
    <>
      <motion.button
        className={`fixed bottom-6 ${isAr ? "left-6" : "right-6"} w-14 h-14 rounded-full bg-gradient-to-r from-[var(--color-gold)] to-[var(--color-gold-dim)] flex items-center justify-center shadow-lg hover:shadow-xl z-50 group`}
        onClick={() => setIsOpen(true)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <Sparkles className="text-white w-6 h-6" />
        <span className={`absolute -top-10 bg-[var(--color-bg-card)] border border-[var(--color-border)] text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap ${isAr ? "font-[family-name:var(--font-arabic)]" : ""}`}>
          {dict.ai.floatingTooltip}
        </span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className={`fixed bottom-0 left-0 right-0 h-[60vh] bg-[var(--color-bg-card)] border-t border-[var(--color-border)] z-50 flex flex-col shadow-2xl md:w-[400px] md:rounded-t-xl ${isAr ? "md:left-6 md:right-auto" : "md:right-6 md:left-auto"}`}
            dir={d}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
              <div className="flex items-center gap-2 text-[var(--color-gold)]">
                <Sparkles className="w-5 h-5" />
                <h3 className={`font-bold ${isAr ? "font-[family-name:var(--font-arabic)] text-lg" : "font-[family-name:var(--font-cinzel)]"}`}>
                  {isAr ? "المرشد الآلي" : "Museum Guide"}
                </h3>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-lg max-w-[80%] text-sm ${
                    m.role === "user"
                      ? "bg-[var(--color-gold)] text-[var(--color-bg-primary)] self-end"
                      : `bg-[var(--color-bg-primary)] ${isAr ? "border-r-4" : "border-l-4"} border-[var(--color-gold)] self-start text-[var(--color-text-primary)]`
                  } ${isAr ? "font-[family-name:var(--font-arabic)]" : ""}`}
                >
                  {m.role === "ai" && (
                    <div className="text-[10px] opacity-60 mb-1">{dict.ai.senderName} 🤖</div>
                  )}
                  {m.content}
                </div>
              ))}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-bg-primary)]">
              <div className="flex items-center gap-2">
                <button 
                  onMouseDown={startRecording}
                  onMouseUp={stopRecording}
                  onTouchStart={startRecording}
                  onTouchEnd={stopRecording}
                  className={`p-2 rounded-full transition-colors ${
                    isRecording 
                      ? "bg-red-500 text-white animate-pulse" 
                      : "bg-[var(--color-bg-card)] text-[var(--color-text-secondary)] hover:text-[var(--color-gold)]"
                  }`}
                >
                  <Mic className="w-5 h-5" />
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && send(input)}
                  placeholder={isRecording ? (isAr ? 'جاري التسجيل...' : 'Recording...') : dict.detail.inputPlaceholder}
                  dir={d}
                  disabled={isRecording}
                  className={`flex-1 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-full px-4 py-2 text-sm focus:outline-none focus:border-[var(--color-gold)] text-[var(--color-text-primary)] ${isAr ? "font-[family-name:var(--font-arabic)]" : ""}`}
                />
                <button
                  onClick={() => send(input)}
                  disabled={isRecording}
                  className="p-2 rounded-full bg-[var(--color-gold)] text-[var(--color-bg-primary)] disabled:opacity-50"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
