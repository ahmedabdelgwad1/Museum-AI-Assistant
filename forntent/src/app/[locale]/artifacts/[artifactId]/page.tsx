import { PageTransition } from "@/components/layout/PageTransition";
import { ChatPanel } from "@/components/features/chat/ChatPanel";
import { getDictionary } from "@/lib/dictionaries";
import { getArtifact } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";

export default async function ArtifactDetailPage({ params }: { params: Promise<{ locale: string, artifactId: string }> }) {
  const p = await params;
  const locale = p.locale as "en" | "ar";
  const artifactId = p.artifactId;
  const dict = getDictionary(locale);

  let artifact: any = null;
  try {
    artifact = await getArtifact(artifactId);
  } catch (e) {
    console.error(e);
  }

  if (!artifact) {
    artifact = {
      id: artifactId,
      artifact_name_en: "Golden Mask of Tutankhamun",
      artifact_name_ar: "القناع الذهبي للملك توت عنخ آمون",
      description_en: "The mask of Tutankhamun is a gold death mask of the 18th-dynasty ancient Egyptian Pharaoh Tutankhamun (reigned 1332–1323 BC). It was discovered by Howard Carter in 1925 in tomb KV62 in the Valley of the Kings, and is now housed in the Egyptian Museum in Cairo. The mask is one of the most well-known works of art in the world.",
      description_ar: "قناع توت عنخ آمون هو قناع جنائزي ذهبي للفرعون المصري القديم توت عنخ آمون (الذي حكم 1332-1323 قبل الميلاد). اكتشفه هوارد كارتر في عام 1925 في المقبرة KV62 في وادي الملوك، وهو الآن محفوظ في المتحف المصري بالقاهرة.",
      category_en: "Mask",
      category_ar: "قناع",
      discovery_site_en: "Valley of the Kings",
      discovery_site_ar: "وادي الملوك",
      hall_en: "Royal Hall",
      hall_ar: "القاعة الملكية",
      link: "#"
    };
  }

  const name = locale === 'en' ? artifact.artifact_name_en : artifact.artifact_name_ar;
  const description = locale === 'en' ? artifact.description_en : artifact.description_ar;

  return (
    <PageTransition>
      <div className="min-h-screen bg-[var(--color-bg-primary)] papyrus-texture w-full flex flex-col md:flex-row">
        
        {/* Left Column - Details */}
        <div className="flex-1 md:w-[60%] p-6 relative overflow-y-auto pb-24 md:pb-6">
          <div className="flex justify-between items-center mb-6">
            <Link href={`/${locale}/sections/${artifact.section_number || 38}`} className="inline-block text-[var(--color-gold)] hover:text-[var(--color-gold-light)] font-sans text-sm">
              {dict.detail.back}
            </Link>
            <Link href={`/${locale}/welcome`} className="flex items-center justify-center text-sm border border-[var(--color-border)] w-8 h-8 rounded hover:border-[var(--color-gold)] text-[var(--color-text-secondary)] hover:text-[var(--color-gold)] transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            </Link>
          </div>

          <div className="relative w-full h-[300px] md:h-[400px] border border-[var(--color-border)] rounded-xl overflow-hidden mb-8 shadow-[0_0_20px_rgba(201,168,76,0.1)] p-1 bg-[var(--color-bg-card)]">
            {artifact.image_url ? (
              <div className="relative w-full h-full rounded-lg overflow-hidden">
                <Image 
                  src={artifact.image_url} 
                  alt={name || ""} 
                  fill 
                  className="object-cover"
                  unoptimized
                />
              </div>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center opacity-20 border border-dashed border-[var(--color-gold)] rounded-lg">
                <svg viewBox="0 0 100 100" width="80" height="80" fill="var(--color-gold)">
                  <path d="M50 20C20 20 5 50 5 50C5 50 20 80 50 80C80 80 95 50 95 50C95 50 80 20 50 20ZM50 70C38.95 70 30 61.05 30 50C30 38.95 38.95 30 50 30C61.05 30 70 38.95 70 50C70 61.05 61.05 70 50 70Z"></path>
                </svg>
              </div>
            )}
          </div>

          <h1 className={`text-4xl text-[var(--color-gold)] mb-2 leading-tight ${locale === 'ar' ? 'font-[family-name:var(--font-noto-naskh)] text-right' : 'font-[family-name:var(--font-cinzel)]'}`}>
            {locale === 'en' ? artifact.artifact_name_en : artifact.artifact_name_ar}
          </h1>
          <h2 className={`text-xl text-[var(--color-text-secondary)] mb-6 ${locale === 'ar' ? 'font-[family-name:var(--font-cinzel)] text-right' : 'font-[family-name:var(--font-noto-naskh)] text-2xl'}`}>
            {locale === 'ar' ? artifact.artifact_name_en : artifact.artifact_name_ar}
          </h2>

          <div className="flex flex-wrap gap-3 mb-8">
            {[
              { icon: '🏛️', text: locale === 'en' ? artifact.hall_en : artifact.hall_ar },
              { icon: '📍', text: locale === 'en' ? artifact.discovery_site_en : artifact.discovery_site_ar },
              { icon: '🏷️', text: locale === 'en' ? artifact.category_en : artifact.category_ar },
            ].map((pill, i) => (
              <div key={i} className="bg-[var(--color-bg-card)] border border-[var(--color-gold)] px-3 py-1 rounded-full text-xs flex items-center gap-2" dir="ltr">
                <span>{pill.icon}</span>
                <span className="text-[var(--color-text-primary)] font-sans">{pill.text}</span>
              </div>
            ))}
          </div>

          <div className="prose prose-invert max-w-none text-[var(--color-text-primary)] font-[family-name:var(--font-body)] text-lg leading-relaxed mb-8">
            <p>{description}</p>
          </div>
        </div>

        {/* Right Column - Chat Panel */}
        <div className="w-full md:w-[40%] bg-[var(--color-bg-card)] md:h-screen sticky top-0 border-t md:border-t-0 md:border-l border-[var(--color-border)] shadow-[-10px_0_20px_rgba(0,0,0,0.2)]">
          <ChatPanel artifact={artifact} locale={locale} />
        </div>

      </div>
    </PageTransition>
  );
}
