"use client";
import { PageTransition } from "@/components/layout/PageTransition";
import { FloatingAIButton } from "@/components/layout/FloatingAIButton";
import { SectionCard } from "@/components/features/sections/SectionCard";
import { getDictionary } from "@/lib/dictionaries";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

interface SectionData {
  id: number | string;
  nameEn: string;
  nameAr: string;
  icon: string;
  count: number;
}

export default function SectionsPage({ params }: { params: Promise<{ locale: string }> }) {
  const p = use(params);
  const locale = p.locale as "en" | "ar";
  const dict = getDictionary(locale);
  const otherLocale = locale === 'en' ? 'ar' : 'en';
  const otherLocaleLabel = locale === 'en' ? 'عربي' : 'English';

  const [sections, setSections] = useState<SectionData[]>([]);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  useEffect(() => {
    async function fetchSections() {
      const { data } = await supabase
        .from('museum_artifacts')
        .select('metadata');
      
      if (data) {
        const sectionsMap = new Map<string, SectionData>();
        
        data.forEach(item => {
           const meta = typeof item.metadata === 'string' ? JSON.parse(item.metadata) : item.metadata;
           
           // Ensure we have a valid section
           const sectionNum = meta?.section_number?.toString()?.trim();
           if (sectionNum && sectionNum !== "nan" && sectionNum !== "") {
             if (sectionsMap.has(sectionNum)) {
               const existing = sectionsMap.get(sectionNum)!;
               existing.count += 1;
             } else {
               sectionsMap.set(sectionNum, {
                 id: sectionNum,
                 nameEn: meta.section_name_en || `Section ${sectionNum}`,
                 nameAr: meta.section_name_ar || `قسم ${sectionNum}`,
                 icon: "column", // Default icon
                 count: 1
               });
             }
           }
        });
        
        const sortedSections = Array.from(sectionsMap.values()).sort((a, b) => b.count - a.count);
        setSections(sortedSections);
      }
      setLoading(false);
    }
    
    fetchSections();
  }, []);

  return (
    <PageTransition>
      <div className="min-h-screen bg-[var(--color-bg-primary)] papyrus-texture w-full flex flex-col">
        {/* Header */}
        <header className="sticky top-0 z-40 bg-[var(--color-bg-secondary)]/90 backdrop-blur border-b border-[var(--color-gold)] p-4 flex justify-between items-center">
          <div className={`text-[var(--color-gold)] text-sm tracking-widest ${locale === 'ar' ? 'font-[family-name:var(--font-noto-naskh)] text-base' : 'font-[family-name:var(--font-cinzel)]'}`}>
            {locale === 'ar' ? 'مكتبة الإسكندرية' : 'Bibliotheca Alexandrina'}
          </div>
          <div className="flex items-center gap-3">
            <Link href={`/${locale}/welcome`} className="flex items-center justify-center text-sm border border-[var(--color-border)] w-8 h-8 rounded hover:border-[var(--color-gold)] text-[var(--color-text-secondary)] hover:text-[var(--color-gold)] transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            </Link>
            <Link href={`/${otherLocale}/sections`} className="text-sm border border-[var(--color-border)] px-3 py-1 rounded hover:border-[var(--color-gold)] text-[var(--color-text-secondary)] hover:text-[var(--color-gold)] transition-colors font-sans">
              {otherLocaleLabel}
            </Link>
          </div>
        </header>

        <main className="flex-1 max-w-[1280px] w-full mx-auto px-6 py-12">
          <div className="text-center mb-12">
            <h1 className={`text-4xl text-[var(--color-text-primary)] mb-4 ${locale === 'ar' ? 'font-[family-name:var(--font-noto-naskh)]' : 'font-[family-name:var(--font-cinzel)]'}`}>
              {dict.sections.title}
            </h1>
            <div className="h-px w-24 bg-[var(--color-gold)] mx-auto"></div>
          </div>

          {loading ? (
             <div className="w-full text-center py-20 text-[var(--color-text-secondary)]">Loading sections...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {sections.map((section) => (
                <SectionCard key={section.id} section={section} locale={locale} />
              ))}
            </div>
          )}
        </main>
        
        <FloatingAIButton locale={locale} />
      </div>
    </PageTransition>
  );
}
