"use client";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { ArrowRight, ArrowLeft } from "lucide-react";

export function ArtifactCard({ artifact, locale, index = 0 }: { artifact: any; locale: "en" | "ar", index?: number }) {
  const router = useRouter();
  const name = locale === 'en' ? artifact.artifact_name_en : artifact.artifact_name_ar;
  const hall = locale === 'en' ? artifact.hall_en : artifact.hall_ar;
  const isAr = locale === 'ar';

  return (
    <div
      onClick={() => router.push(`/${locale}/artifacts/${artifact.id}`)}
      // Use data-odd for CSS-only stagger so SSR and client always match.
      // Avoid computing className dynamically from index — that causes
      // React hydration mismatches when SSR and client disagree on index.
      data-odd={index % 2 !== 0 ? "true" : undefined}
      className="group relative bg-bg-secondary/80 backdrop-blur-xl border border-border hover:border-primary transition-colors duration-500 overflow-hidden cursor-pointer flex flex-col h-[400px] data-odd:lg:mt-8"
    >

      <div className="h-[60%] overflow-hidden relative">
        {artifact.image_url ? (
          <Image 
            src={artifact.image_url} 
            alt={name || ""} 
            fill 
            className="object-cover transform group-hover:scale-110 transition-transform duration-1000 ease-in-out opacity-80 group-hover:opacity-100"
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center opacity-20 bg-black/40">
            <svg viewBox="0 0 100 100" width="40" height="40" fill="vargold">
              <path d="M50 20C20 20 5 50 5 50C5 50 20 80 50 80C80 80 95 50 95 50C95 50 80 20 50 20ZM50 70C38.95 70 30 61.05 30 50C30 38.95 38.95 30 50 30C61.05 30 70 38.95 70 50C70 61.05 61.05 70 50 70Z"></path>
            </svg>
          </div>
        )}
        {/* Dark gradient fade over image bottom */}
        <div className="absolute inset-0 bg-linear-to-t from-bg-secondary to-transparent"></div>
      </div>
      
      <div className={`h-[40%] p-6 flex flex-col justify-between relative z-10 bg-linear-to-b from-bg-secondary to-[#1a1924] ${isAr ? 'text-right' : ''}`}>
        <div>
          <h3 className={`text-xl text-text-primary mb-2 ${isAr ? 'font-(family-name:--font-almarai)' : 'font-(family-name:--font-inter)'}`}>
            {name || (isAr ? 'قطعة غير معروفة' : 'Unknown Artifact')}
          </h3>
          <p className={`text-sm text-text-secondary ${isAr ? 'font-(family-name:--font-almarai)' : 'font-sans'}`}>{hall}</p>
        </div>
        
        {/* Animated Action Label */}
        <div className={`font-(family-name:--font-label-sm) text-[12px] tracking-[0.2em] text-primary opacity-0 group-hover:opacity-100 transition-all duration-500 translate-y-2 group-hover:translate-y-0 uppercase flex items-center gap-2 ${isAr ? 'flex-row-reverse' : ''}`}>
          {isAr ? 'عرض التفاصيل' : 'View Details'} 
          {isAr ? <ArrowLeft size={16} /> : <ArrowRight size={16} />}
        </div>
      </div>
    </div>
  );
}
