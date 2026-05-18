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

  // High quality images from the Stitch design
  const STITCH_IMAGES = [
    "https://lh3.googleusercontent.com/aida-public/AB6AXuAhROrevFarT9SAER_RuSVymsFApiTg6ZevaYJQ4zEl8RNyYP1QNErtYn6cGDUKqESNPrR8qO01URfpg866H_YfpPmNqYU_iW8YbGAFx0sEty-sue_2FxUnGg7zJL7CFdwuz9Hh03HyqclVousYFW-voIdTuZZ_xSiuJ0PSDmHWVajmusa05JHiLfmYdvQysS60Xtmr3MZvdg-AAwWF_5ql8lFf5lwWjPKmauYh5DE_AwJv9Augu1dYvzybtDvzKHKi2CoG3Sw183OF",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDnVnEJOV7f67-JBX-L7xMw1GW1wYRzPp-3ghDFoO3-S5ngWoH0Podlk0qn2WOJY2HyHgHjFedak6krquX2rqLv6g-YO_oC37D0YM4d-jQKGCTPhZLdJt6lZ7xlZsy8qgr9lVQEv13jIVPcmqGgKQX8WZ3kBFZW-3fRq2-dedZsAR3TMCzrNY6VOGxArdntAYuyTKrvQVFOHAQLjv75rATCjGy2kLjHSqKqGY2hobxQq4sNl05UnlnKp2nZGiwBoTk_12FpmCm9OD19",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBSzfdBTaxs4ZOLygr18MfUMbaZ05AM0Y22lk8VyX2C4971mNEsA1zT83XgxktypaEMWBkcRf5gA8dAxtOn2CdzYQRuXvxlYqMJwX9cRk4p2c31dlBPvPuPWAjJGfRjNkuPRq_Q8DGjdZkUM3RE9VvGP27LbksLBrofDtbw13uj9tRjziwKP47aYqUWHfmmuxG_8KryoJ7F1qvXJwYqKq1tqk16KY6DIJ3RH_A5Bo8ST8VOb6A-Cj5QwgUtTT1bdFwM6F6IJAXsDD1H",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDlCv4xtBPsys-QYyhHFkZyVEkkTiy5jjV1gcAa3EW8oTKJ0ZFWjE_1sMpWWjQ-4CxE5pN8Nvy68QxnrYD5JcnZR6zrRaDkNgZzghQV2-HjzXpKdog5EGHratQLXlktj5IYDhMUkklhTCxD0lLU4hniHEdm3Rlr7NGAko7OlYkzskOSRoZMby9M4k0s9XUj_k-Wfr0ceyEyYauvKNBv0EqHbb6GCFzia1BRC8EQLQOcOAbuGI8TGOCjHDi1Wc5Rtxoy0h2Uj9Vu5RbV"
  ];

  if (!Array.isArray(artifacts) || artifacts.length === 0) {
    artifacts = Array.from({ length: 8 }).map((_, i) => ({
      id: `${i}`,
      section_number: parseInt(sectionId),
      artifact_name_en: `Artifact ${i + 1}`,
      artifact_name_ar: `القطعة ${i + 1}`,
      hall_en: "Main Hall",
      hall_ar: "القاعة الرئيسية",
      image_url: STITCH_IMAGES[i % 4]
    }));
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
