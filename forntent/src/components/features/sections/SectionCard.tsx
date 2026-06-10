"use client";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Coins, Book, Building, Landmark } from "lucide-react";

interface Section {
  id: number | string;
  nameEn: string;
  nameAr: string;
  icon: string;
  count: number;
}

export function SectionCard({ section, locale }: { section: Section; locale: "en" | "ar" }) {
  const router = useRouter();

  const icon = (() => {
    switch (section.icon) {
      case 'ankh': return <Landmark className="w-12 h-12 text-gold" />;
      case 'column': return <Building className="w-12 h-12 text-gold" />;
      case 'crescent': return <Book className="w-12 h-12 text-gold" />;
      case 'coin': return <Coins className="w-12 h-12 text-gold" />;
      default: return <Landmark className="w-12 h-12 text-gold" />;
    }
  })();

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="relative flex flex-col group cursor-pointer bg-bg-card rounded-lg overflow-hidden border-t-4 border-t-gold border-x border-b border-x-border border-b-border hover:shadow-[0_0_15px_rgba(201,168,76,0.3)] transition-shadow duration-300"
      onClick={() => router.push(`/${locale}/sections/${section.id}`)}
    >
      <div className="p-8 flex flex-col items-center justify-center flex-1 bg-linear-to-b from-transparent to-[rgba(0,0,0,0.2)]">
        <motion.div 
          className="mb-6 drop-shadow-[0_0_10px_rgba(201,168,76,0.5)]"
          whileHover={{ scale: 1.1 }}
        >
          {icon}
        </motion.div>
        
        {/* Primary name in active locale */}
        <h3 className={`text-xl text-gold text-center mb-1 ${locale === 'ar' ? 'font-(family-name:--font-almarai)' : 'font-(family-name:--font-inter)'}`}>
          {locale === 'ar' ? section.nameAr : section.nameEn}
        </h3>
        {/* Secondary name dimmed */}
        <h4 className={`text-sm text-text-secondary/60 text-center mb-4 ${locale === 'ar' ? 'font-(family-name:--font-inter)' : 'font-(family-name:--font-almarai)'}`}>
          {locale === 'ar' ? section.nameEn : section.nameAr}
        </h4>
        
        <div className="mt-auto bg-bg-primary px-3 py-1 rounded-full border border-border">
          <span className="text-xs text-text-primary font-sans">
            {locale === 'en' ? `${section.count} artifacts` : `${section.count} قطعه`}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
