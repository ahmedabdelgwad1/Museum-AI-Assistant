"use client";
import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X } from "lucide-react";
import { getDictionary, dir } from "@/lib/dictionaries";
import { RealTimeAIChat } from "@/components/features/chat/RealTimeAIChat";

export function FloatingAIButton({ locale }: { locale: "en" | "ar" }) {
  const [isOpen, setIsOpen] = useState(false);

  const dict = useMemo(() => getDictionary(locale), [locale]);
  const isAr = locale === "ar";
  const d = dir(locale);

  return (
    <>
      <motion.button
        className={`fixed bottom-6 ${isAr ? "left-6" : "right-6"} w-14 h-14 rounded-full bg-linear-to-r from-gold to-gold-dim flex items-center justify-center shadow-lg hover:shadow-xl z-50 group`}
        onClick={() => setIsOpen(true)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        transition={{ duration: 0.2 }}
      >
        <Sparkles className="text-white w-6 h-6" />
        <span
          className={[
            "absolute -top-10 bg-bg-card border border-border text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap",
            isAr ? "font-(family-name:--font-almarai)" : "",
          ].filter(Boolean).join(" ")}
        >
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
            className={`fixed bottom-0 left-0 right-0 h-[78vh] bg-bg-card border-t border-border z-50 flex flex-col shadow-2xl md:w-[430px] md:rounded-t-xl ${isAr ? "md:left-6 md:right-auto" : "md:right-6 md:left-auto"}`}
            dir={d}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <div className="flex items-center gap-2 text-gold">
                <Sparkles className="w-5 h-5" />
                <h3 className={`font-bold ${isAr ? "font-(family-name:--font-almarai) text-lg" : "font-(family-name:--font-inter)"}`}>
                  {isAr ? "المرشد الآلي" : "Museum Guide"}
                </h3>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-text-secondary hover:text-text-primary">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="min-h-0 flex-1">
              <RealTimeAIChat locale={locale} embedded />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
