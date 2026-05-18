"use client";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Coins, Book, Building, Landmark } from "lucide-react";

interface Section {
  id: number;
  nameEn: string;
  nameAr: string;
  icon: string;
  count: number;
}

export function SectionCard({ section, locale }: { section: Section; locale: "en" | "ar" }) {
  const router = useRouter();

  const IconComponent = () => {
    switch (section.icon) {
      case 'ankh': return <Landmark className="w-12 h-12 text-[var(--color-gold)]" />;
      case 'column': return <Building className="w-12 h-12 text-[var(--color-gold)]" />;
      case 'crescent': return <Book className="w-12 h-12 text-[var(--color-gold)]" />;
      case 'coin': return <Coins className="w-12 h-12 text-[var(--color-gold)]" />;
      default: return <Landmark className="w-12 h-12 text-[var(--color-gold)]" />;
    }
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="relative flex flex-col group cursor-pointer bg-[var(--color-bg-card)] rounded-lg overflow-hidden border-t-4 border-t-[var(--color-gold)] border-x border-b border-x-[var(--color-border)] border-b-[var(--color-border)] hover:shadow-[0_0_15px_rgba(201,168,76,0.3)] transition-shadow duration-300"
      onClick={() => router.push(`/${locale}/sections/${section.id}`)}
    >
      <div className="p-8 flex flex-col items-center justify-center flex-1 bg-gradient-to-b from-transparent to-[rgba(0,0,0,0.2)]">
        <motion.div 
          className="mb-6 drop-shadow-[0_0_10px_rgba(201,168,76,0.5)]"
          whileHover={{ scale: 1.1 }}
        >
          <IconComponent />
        </motion.div>
        
        {/* Primary name in active locale */}
        <h3 className={`text-xl text-[var(--color-gold)] text-center mb-1 ${locale === 'ar' ? 'font-[family-name:var(--font-noto-naskh)]' : 'font-[family-name:var(--font-cinzel)]'}`}>
          {locale === 'ar' ? section.nameAr : section.nameEn}
        </h3>
        {/* Secondary name dimmed */}
        <h4 className={`text-sm text-[var(--color-text-secondary)]/60 text-center mb-4 ${locale === 'ar' ? 'font-[family-name:var(--font-cinzel)]' : 'font-[family-name:var(--font-noto-naskh)]'}`}>
          {locale === 'ar' ? section.nameEn : section.nameAr}
        </h4>
        
        <div className="mt-auto bg-[var(--color-bg-primary)] px-3 py-1 rounded-full border border-[var(--color-border)]">
          <span className="text-xs text-[var(--color-text-primary)] font-sans">
            {locale === 'en' ? `${section.count} artifacts` : `${section.count} قطعه`}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
