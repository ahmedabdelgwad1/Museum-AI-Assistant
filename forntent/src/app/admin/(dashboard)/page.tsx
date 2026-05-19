"use client";
import Image from "next/image";
import { Building2, Clock, MoreHorizontal } from "lucide-react";
import { getDictionary, hFont, bodyFont, dir } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";

import { createClient } from "@/lib/supabase/client";
import { useEffect, useState } from "react";

const L = {
  en: {
    pageTitle: "Curatorial Overview",
    pageSub: "A high-level synthesis of current collection metrics and recent cataloging activities.",
    totalArtifacts: "Total Artifacts",
    recentAcq: "Recent Acquisitions",
    recentAcqSub: "This month",
    pending: "Pending Reviews",
    pendingSub: "Requires attention",
    chartTitle: "Collections Distribution",
    activityTitle: "Recent Activity",
  },
  ar: {
    pageTitle: "نظرة عامة على المقتنيات",
    pageSub: "ملخص شامل لمقاييس المجموعة الحالية وأنشطة الفهرسة الأخيرة.",
    totalArtifacts: "إجمالي القطع الأثرية",
    recentAcq: "الاقتناءات الأخيرة",
    recentAcqSub: "هذا الشهر",
    pending: "المراجعات المعلقة",
    pendingSub: "تتطلب اهتماماً",
    chartTitle: "توزيع المجموعات",
    activityTitle: "النشاط الأخير",
  },
};

const DEFAULT_IMAGE = "https://lh3.googleusercontent.com/aida-public/AB6AXuBA6FlkSGl2M4zEEA3OinZ07qJmwBvRI3Hn1vCCQkuHrizJB7RXQSHITEhDZtz-cJYxOTFB2JLhP_LrTleyttObKZ6KrRxTraIylhVPE2Ck8npsNHYsErkYKZcNOTIioWhZdMH8oQ6n0MSUI3jYYOuaZPdhM_3fk-TpP-nVpaO3-RBlJkM7oq_36irpT5Ni1XBWhukCz4gqoCaYrwKHh2GeDktpARciMtqUeeuvozJUshuODSg2nvY0DC7m0tYG9pJIR_C2EMjpxlU";

export default function AdminDashboard() {
  const { locale } = useAdminLocale();
  const isAr = locale === "ar";
  const t = L[isAr ? "ar" : "en"];

  const [totalArtifacts, setTotalArtifacts] = useState<number>(0);
  const [recentCount, setRecentCount] = useState<number>(0);
  const [sectionsData, setSectionsData] = useState<{name: string, count: number, height: string}[]>([]);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const supabase = createClient();

  useEffect(() => {
    async function fetchStats() {
      // 1. Total Artifacts & Sections Distribution
      const { count, data } = await supabase
        .from('museum_artifacts')
        .select('metadata, created_at', { count: 'exact' });
      
      if (count !== null) {
        setTotalArtifacts(count);
      }

      if (data) {
        // Sections
        const sectionCounts: Record<string, number> = {};
        let monthCount = 0;
        const now = new Date();
        
        data.forEach(item => {
           // Parse metadata
           const meta = typeof item.metadata === 'string' ? JSON.parse(item.metadata) : item.metadata;
           const secName = isAr ? meta?.section_name_ar : meta?.section_name_en;
           if (secName) {
              sectionCounts[secName] = (sectionCounts[secName] || 0) + 1;
           }

           // Check if added this month
           if (item.created_at) {
             const createdAt = new Date(item.created_at);
             if (createdAt.getMonth() === now.getMonth() && createdAt.getFullYear() === now.getFullYear()) {
               monthCount++;
             }
           }
        });
        
        setRecentCount(monthCount);

        const sorted = Object.entries(sectionCounts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5);
          
        const maxCount = sorted.length > 0 ? sorted[0][1] : 1;
        
        const chartData = sorted.map(([name, secCount]) => ({
           name,
           count: secCount,
           height: `${Math.max(15, (secCount / maxCount) * 80)}%`
        }));
        
        setSectionsData(chartData);
      }

      // 2. Recent Activity (last 3 items)
      const { data: recentData } = await supabase
        .from('museum_artifacts')
        .select('id, metadata, created_at')
        .order('created_at', { ascending: false })
        .limit(3);

      if (recentData) {
        const formattedActivity = recentData.map(item => {
          const meta = typeof item.metadata === 'string' ? JSON.parse(item.metadata) : item.metadata;
          const name = isAr ? meta?.artifact_name_ar : meta?.artifact_name_en;
          const hall = meta?.hall || (isAr ? "القاعة الرئيسية" : "Main Hall");
          
          return {
            id: item.id,
            title: name || (isAr ? "قطعة غير معروفة" : "Unknown Artifact"),
            desc: isAr ? `تمت الإضافة إلى ${hall}` : `Added to ${hall}`,
            time: new Date(item.created_at).toLocaleDateString(isAr ? 'ar-EG' : 'en-US'),
            image: meta?.image_url || DEFAULT_IMAGE
          };
        });
        setRecentActivity(formattedActivity);
      }
    }
    fetchStats();
  }, [isAr]);

  return (
    <div dir={dir(locale)} className="flex-1 px-6 md:px-12 pt-10 pb-24 max-w-[1600px] w-full mx-auto relative">
      {/* Noise texture */}
      <div className="absolute inset-0 z-0 opacity-5 pointer-events-none" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'100\' height=\'100\' viewBox=\'0 0 100 100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noise\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.8\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100\' height=\'100\' filter=\'url(%23noise)\' opacity=\'1\'/%3E%3C/svg%3E")' }} />

      {/* Page header */}
      <div className="relative z-10 mb-12">
        <h2 className={`${hFont(locale)} text-3xl text-[var(--color-primary-container)] mb-2`}>{t.pageTitle}</h2>
        <p className={`${bodyFont(locale)} text-xl text-[var(--color-on-surface-variant)] max-w-2xl`}>{t.pageSub}</p>
      </div>

      {/* Bento Grid */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
        {/* Stat Cards */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          {/* Total */}
          <div className="bg-[rgba(26,24,37,0.8)] backdrop-blur border border-[var(--color-gold)]/20 border-t-[var(--color-gold-light)]/60 p-8 relative overflow-hidden group shadow-inner">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Building2 className="w-16 h-16 text-[var(--color-primary-container)]" />
            </div>
            <h3 className={`${hFont(locale)} text-xs uppercase tracking-widest text-[var(--color-on-surface-variant)] mb-4`}>{t.totalArtifacts}</h3>
            <p className="font-[family-name:var(--font-display-lg)] text-6xl font-bold text-[var(--color-primary-container)]">{totalArtifacts}</p>
            <div className="w-12 h-[1px] bg-[var(--color-primary-container)] mt-6" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[rgba(26,24,37,0.8)] backdrop-blur border border-[var(--color-gold)]/20 p-6 flex flex-col justify-between shadow-inner">
              <h3 className={`${hFont(locale)} text-xs uppercase tracking-widest text-[var(--color-on-surface-variant)] mb-2`}>{t.recentAcq}</h3>
              <p className="font-[family-name:var(--font-headline-md)] text-3xl text-[var(--color-surface-tint)]">+{recentCount}</p>
              <p className={`text-xs text-[var(--color-on-surface-variant)] ${bodyFont(locale)} mt-2`}>{t.recentAcqSub}</p>
            </div>
            <div className="bg-[rgba(26,24,37,0.8)] backdrop-blur border border-[var(--color-gold)]/20 border-t-[var(--color-error-container)]/50 p-6 flex flex-col justify-between shadow-inner">
              <h3 className={`${hFont(locale)} text-xs uppercase tracking-widest text-[var(--color-on-surface-variant)] mb-2`}>{t.pending}</h3>
              <p className="font-[family-name:var(--font-headline-md)] text-3xl text-[var(--color-error-container)]">0</p>
              <p className={`text-xs text-[var(--color-on-surface-variant)] ${bodyFont(locale)} mt-2`}>{isAr ? "الكل مراجع!" : "All caught up!"}</p>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="lg:col-span-8 bg-[rgba(26,24,37,0.8)] backdrop-blur border border-[var(--color-gold)]/20 p-8 flex flex-col shadow-inner">
          <div className="flex justify-between items-center mb-8">
            <h3 className={`${hFont(locale)} text-xs uppercase tracking-widest text-[var(--color-primary-container)]`}>{t.chartTitle}</h3>
            <button className="text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary-container)] transition-colors">
              <MoreHorizontal size={24} />
            </button>
          </div>
          <div className="flex items-end gap-4 h-56 border-l border-b border-[var(--color-outline-variant)]/30 pb-4 px-4">
            {sectionsData.length > 0 ? (
              sectionsData.map((bar, i) => (
                <div key={i} className="flex flex-col items-center gap-2 group w-full px-1">
                  <div
                    className="w-full bg-[var(--color-primary-container)]/20 border border-[var(--color-primary-container)]/50 group-hover:bg-[var(--color-primary-container)]/40 transition-colors relative cursor-pointer"
                    style={{ height: bar.height }}
                  >
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 font-[family-name:var(--font-label-sm)] text-[var(--color-primary-container)] transition-opacity text-xs">
                      {bar.count}
                    </div>
                  </div>
                  <span className={`text-[10px] uppercase text-[var(--color-on-surface-variant)] hidden sm:block ${hFont(locale)} truncate max-w-full text-center`} title={bar.name}>
                    {bar.name.substring(0, 15)}{bar.name.length > 15 ? '...' : ''}
                  </span>
                </div>
              ))
            ) : (
               <div className="w-full text-center text-sm text-[var(--color-on-surface-variant)] self-center">Loading...</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="relative z-10">
        <h3 className={`${hFont(locale)} text-xs uppercase tracking-widest text-[var(--color-primary-container)] mb-6 flex items-center gap-2`}>
          <Clock size={16} /> {t.activityTitle}
        </h3>
        <div className="flex flex-col gap-4">
          {recentActivity.map((item) => (
            <div key={item.id} className="bg-[rgba(26,24,37,0.8)] backdrop-blur border border-[var(--color-gold)]/20 p-4 flex items-center gap-5 hover:border-[var(--color-primary-container)]/50 transition-colors cursor-pointer group shadow-inner">
              <div className="w-16 h-16 border border-[var(--color-primary-container)]/30 p-1 shrink-0">
                <div className="relative w-full h-full grayscale group-hover:grayscale-0 transition-all duration-500">
                  <Image src={item.image} alt={item.title} fill className="object-cover" unoptimized />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className={`${hFont(locale)} text-lg text-[var(--color-on-surface)] truncate`}>{item.title}</h4>
                <p className={`${bodyFont(locale)} text-sm text-[var(--color-on-surface-variant)] truncate`}>{item.desc}</p>
              </div>
              <div className={`text-right hidden sm:block shrink-0`}>
                <p className={`${hFont(locale)} text-xs text-[var(--color-on-surface-variant)] uppercase tracking-widest`}>{item.time}</p>
                <span className={`inline-block mt-2 px-2 py-1 ${hFont(locale)} text-[10px] border tracking-wider uppercase text-[var(--color-primary-container)] border-[var(--color-primary-container)]/20 bg-[var(--color-primary-container)]/10`}>
                  {isAr ? "جديد" : "NEW"}
                </span>
              </div>
            </div>
          ))}
          {recentActivity.length === 0 && (
            <div className="text-[var(--color-on-surface-variant)] text-sm">{isAr ? "لا يوجد نشاط أخير." : "No recent activity."}</div>
          )}
        </div>
      </div>
    </div>
  );
}
