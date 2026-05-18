"use client";
import { useRouter } from "next/navigation";
import { useMuseumStore } from "@/lib/store";
import { PageTransition } from "@/components/layout/PageTransition";
import { getDictionary } from "@/lib/dictionaries";
import { use } from "react";

export default function WelcomePage({ params }: { params: Promise<{ locale: string }> }) {
  const router = useRouter();
  const { setLanguage } = useMuseumStore();
  const p = use(params);
  const locale = p.locale as "en" | "ar";
  const dict = getDictionary(locale);

  const handleLanguageSelect = (lang: "en" | "ar") => {
    setLanguage(lang);
    router.push(`/${lang}/sections`);
  };

  return (
    <PageTransition>
      <main className="z-10 flex flex-col items-center justify-center min-h-screen text-center px-6 py-12 w-full relative overflow-hidden papyrus-texture">
        {/* Background elements */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(201,168,76,0.05)_0%,transparent_50%)] pointer-events-none z-0"></div>
        <div className="absolute top-1/4 left-1/4 w-1 h-1 bg-[var(--color-gold)] rounded-full opacity-30 shadow-[0_0_10px_#c9a84c]"></div>
        <div className="absolute top-3/4 right-1/3 w-1.5 h-1.5 bg-[var(--color-gold)] rounded-full opacity-20 shadow-[0_0_15px_#c9a84c]"></div>
        <div className="absolute top-1/2 right-1/4 w-0.5 h-0.5 bg-[var(--color-gold)] rounded-full opacity-40 shadow-[0_0_5px_#c9a84c]"></div>
        <div className="absolute bottom-1/4 left-1/3 w-1 h-1 bg-[var(--color-gold)] rounded-full opacity-25 shadow-[0_0_8px_#c9a84c]"></div>

        <div className="z-10 flex flex-col items-center max-w-[800px] w-full">
          {/* Eye of Horus SVG */}
          <div className="mb-8 text-[var(--color-gold)] drop-shadow-[0_0_15px_rgba(201,168,76,0.3)]">
            <svg fill="currentColor" height="80" viewBox="0 0 100 100" width="80" xmlns="http://www.w3.org/2000/svg">
              <path d="M50 20C20 20 5 50 5 50C5 50 20 80 50 80C80 80 95 50 95 50C95 50 80 20 50 20ZM50 70C38.95 70 30 61.05 30 50C30 38.95 38.95 30 50 30C61.05 30 70 38.95 70 50C70 61.05 61.05 70 50 70Z"></path>
              <circle cx="50" cy="50" fill="currentColor" r="12"></circle>
              <path d="M50 80 L50 95 M30 75 L20 90" stroke="currentColor" strokeLinecap="round" strokeWidth="4"></path>
            </svg>
          </div>

          <h1 className={`text-4xl md:text-6xl text-[var(--color-gold)] uppercase mb-4 tracking-[0.1em] drop-shadow-[0_2px_10px_rgba(201,168,76,0.2)] ${locale === 'ar' ? 'font-[family-name:var(--font-arabic)]' : 'font-[family-name:var(--font-cinzel)]'}`}>
            {dict.welcome.title}
          </h1>
          <h2 className={`text-xl md:text-2xl text-[var(--color-sand)] italic tracking-widest mb-12 ${locale === 'ar' ? 'font-[family-name:var(--font-arabic)]' : 'font-[family-name:var(--font-cormorant)]'}`}>
            {dict.welcome.subtitle}
          </h2>

          {/* Divider */}
          <div className="flex items-center w-full max-w-[300px] mb-16 opacity-60">
            <div className="h-px bg-gradient-to-r from-transparent via-[var(--color-gold)] to-transparent flex-1"></div>
            <div className="mx-4 text-[var(--color-gold)] text-xs tracking-[0.3em] font-[family-name:var(--font-cinzel)]">✦</div>
            <div className="h-px bg-gradient-to-r from-transparent via-[var(--color-gold)] to-transparent flex-1"></div>
          </div>

          <p className="text-[var(--color-text-secondary)] mb-6 tracking-widest uppercase text-sm font-sans">
            {dict.welcome.chooseLanguage}
          </p>

          <div className="flex flex-col sm:flex-row gap-6 w-full max-w-[400px]">
            {/* English Button */}
            <button 
              onClick={() => handleLanguageSelect('en')}
              className="flex-1 group relative overflow-hidden bg-[#1a1825]/80 backdrop-blur-[20px] border border-[rgba(201,168,76,0.2)] hover:border-[var(--color-gold)] rounded p-6 transition-all duration-300 shadow-[inset_0_1px_0_rgba(201,168,76,0.1)] hover:shadow-[0_0_20px_rgba(201,168,76,0.15)] flex flex-col items-center justify-center cursor-pointer"
            >
              <div className="absolute inset-0 bg-gradient-to-b from-[var(--color-gold)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="font-[family-name:var(--font-cinzel)] text-sm text-[var(--color-text-primary)] uppercase tracking-widest z-10 group-hover:text-[var(--color-gold)] transition-colors">
                English
              </span>
              <span className="mt-2 text-[10px] text-[var(--color-text-secondary)] tracking-wider uppercase font-sans z-10">Enter Museum</span>
            </button>

            {/* Arabic Button */}
            <button 
              onClick={() => handleLanguageSelect('ar')}
              className="flex-1 group relative overflow-hidden bg-[#1a1825]/80 backdrop-blur-[20px] border border-[rgba(201,168,76,0.2)] hover:border-[var(--color-gold)] rounded p-6 transition-all duration-300 shadow-[inset_0_1px_0_rgba(201,168,76,0.1)] hover:shadow-[0_0_20px_rgba(201,168,76,0.15)] flex flex-col items-center justify-center cursor-pointer"
              dir="rtl"
            >
              <div className="absolute inset-0 bg-gradient-to-b from-[var(--color-gold)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="font-[family-name:var(--font-noto-naskh)] text-2xl text-[var(--color-text-primary)] z-10 group-hover:text-[var(--color-gold)] transition-colors">
                عربي
              </span>
              <span className="mt-1 text-[10px] text-[var(--color-text-secondary)] tracking-wider uppercase font-sans z-10">دخول المتحف</span>
            </button>
          </div>
        </div>

        <footer className="absolute bottom-8 left-0 w-full text-center z-10 flex flex-col items-center gap-2">
          <p className="font-[family-name:var(--font-cinzel)] text-[rgba(201,168,76,0.5)] uppercase tracking-[0.2em] text-[10px]">
            Bibliotheca Alexandrina © 2024
          </p>
          <a href="/admin/login" className="font-[family-name:var(--font-cinzel)] text-[rgba(201,168,76,0.3)] hover:text-[rgba(201,168,76,0.8)] uppercase tracking-[0.2em] text-[10px] transition-colors">
            {locale === 'ar' ? 'بوابة الإدارة' : 'Admin Portal'}
          </a>
        </footer>
      </main>
    </PageTransition>
  );
}
