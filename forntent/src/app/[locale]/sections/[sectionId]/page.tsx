import { PageTransition } from "@/components/layout/PageTransition";
import { FloatingAIButton } from "@/components/layout/FloatingAIButton";
import { ArtifactCard } from "@/components/features/artifacts/ArtifactCard";
import { getDictionary } from "@/lib/dictionaries";
import { getArtifacts } from "@/lib/api";
import Link from "next/link";
import { Search } from "lucide-react";

// Map section IDs → localized names & icons
const SECTION_META: Record<string, { en: string; ar: string; icon: string }> = {
  "38": { en: "Ancient Egyptian Antiquities", ar: "الآثار المصرية القديمة",      icon: "🏺" },
  "39": { en: "Greco-Roman Antiquities",      ar: "الآثار اليونانية والرومانية", icon: "🏛️" },
  "40": { en: "Islamic Antiquities",           ar: "الآثار الإسلامية",            icon: "🕌" },
  "41": { en: "Coins Collection",             ar: "مجموعة العملات",              icon: "🪙" },
};

export default async function ArtifactsPage({
  params,
}: {
  params: Promise<{ locale: string; sectionId: string }>;
}) {
  const p = await params;
  const locale = p.locale as "en" | "ar";
  const sectionId = p.sectionId;
  const dict = getDictionary(locale);
  const isAr = locale === "ar";

  const meta = SECTION_META[sectionId] ?? {
    en: `Collection ${sectionId}`,
    ar: `المجموعة ${sectionId}`,
    icon: "🏛️",
  };
  const sectionName = isAr ? meta.ar : meta.en;

  let artifacts: any[] = [];
  try {
    artifacts = await getArtifacts(parseInt(sectionId));
  } catch (e) {
    console.error(e);
  }


  if (!Array.isArray(artifacts) || artifacts.length === 0) {
    return (
      <PageTransition>
        <div className="min-h-screen bg-[var(--color-bg-primary)] papyrus-texture w-full flex flex-col items-center justify-center">
          <p className="text-[var(--color-gold)] text-6xl mb-4">🏛️</p>
          <h1 className="text-2xl text-[var(--color-text-primary)] font-[family-name:var(--font-cinzel)] mb-2">No Artifacts Found</h1>
          <p className="text-[var(--color-text-secondary)] mb-6">
            {isAr ? "تعذّر تحميل البيانات. قد يكون الخادم غير متاح." : "Could not load artifacts. The server may be offline."}
          </p>
          <Link href={`/${locale}/sections`} className="text-[var(--color-gold)] border border-[var(--color-gold)] px-4 py-2 rounded hover:bg-[var(--color-gold)] hover:text-black transition-colors">
            {isAr ? "العودة للمجموعات" : "Back to Collections"}
          </Link>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div
        dir={isAr ? "rtl" : "ltr"}
        className="min-h-screen bg-[var(--color-bg-primary)] papyrus-texture w-full flex flex-col"
      >
        {/* Header */}
        <header className="sticky top-0 z-40 bg-[var(--color-bg-secondary)]/90 backdrop-blur border-b border-[var(--color-gold)] p-4 flex items-center justify-between">
          <Link
            href={`/${locale}/sections`}
            className={`text-[var(--color-gold)] hover:text-[var(--color-gold-light)] flex items-center gap-2 text-sm ${isAr ? "font-[family-name:var(--font-arabic)] flex-row-reverse" : "font-sans"}`}
          >
            {dict.artifacts.backToCollections}
          </Link>
          <Link href={`/${locale}/welcome`} className="flex items-center justify-center text-sm border border-[var(--color-border)] w-8 h-8 rounded hover:border-[var(--color-gold)] text-[var(--color-text-secondary)] hover:text-[var(--color-gold)] transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          </Link>
        </header>

        <main className="flex-1 max-w-[1280px] w-full mx-auto px-6 py-8">
          {/* Section Title */}
          <div className="text-center mb-10">
            <div className="w-16 h-16 mx-auto bg-[var(--color-bg-card)] rounded-full flex items-center justify-center border border-[var(--color-gold)] mb-4 shadow-[0_0_15px_rgba(201,168,76,0.15)]">
              <span className="text-2xl">{meta.icon}</span>
            </div>
            <h1
              className={`text-3xl text-[var(--color-text-primary)] mb-4 ${isAr ? "font-[family-name:var(--font-arabic)]" : "font-[family-name:var(--font-cinzel)]"}`}
            >
              {sectionName}
            </h1>
            <div className="h-px w-32 bg-[var(--color-gold)] mx-auto opacity-50" />
          </div>

          {/* Search */}
          <div className="max-w-2xl mx-auto mb-12 relative group">
            <Search
              className={`absolute ${isAr ? "right-4" : "left-4"} top-1/2 -translate-y-1/2 text-[var(--color-gold)] w-5 h-5`}
            />
            <input
              type="text"
              placeholder={dict.artifacts.searchPlaceholder}
              dir={isAr ? "rtl" : "ltr"}
              className={`w-full bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-full py-3 ${isAr ? "pr-12 pl-4 font-[family-name:var(--font-arabic)] text-right" : "pl-12 pr-4"} text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-gold)] transition-colors group-hover:shadow-[0_0_15px_rgba(201,168,76,0.1)]`}
            />
          </div>

          {/* Artifacts Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-24">
            {artifacts.map((art: any, index: number) => (
              <ArtifactCard key={art.id} artifact={art} locale={locale} index={index} />
            ))}
          </div>
        </main>

        <FloatingAIButton locale={locale} />
      </div>
    </PageTransition>
  );
}
