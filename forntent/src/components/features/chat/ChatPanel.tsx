"use client";
import { RealTimeAIChat } from "@/components/features/chat/RealTimeAIChat";

type ChatPanelArtifact = {
  artifact_name_en?: string;
  artifact_name_ar?: string;
} | null;

export function ChatPanel({ artifact, locale }: { artifact: ChatPanelArtifact; locale: "en" | "ar" }) {
  return (
    <div className="sticky top-0 flex h-[600px] flex-col border-l border-border bg-bg-card md:h-screen">
      <RealTimeAIChat artifact={artifact} locale={locale} embedded />
    </div>
  );
}
