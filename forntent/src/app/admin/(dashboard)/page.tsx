"use client";
import Image from "next/image";
import { Building2, Clock, MoreHorizontal } from "lucide-react";
import { getDictionary, hFont, bodyFont, dir } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";

const L = {
  en: {
    pageTitle: "Curatorial Overview",
    pageSub: "A high-level synthesis of current collection metrics and recent cataloging activities.",
    totalArtifacts: "Total Artifacts",
    recentAcq: "Recent Acquisitions",
    recentAcqSub: "+3 this month",
    pending: "Pending Reviews",
    pendingSub: "Requires attention",
    chartTitle: "Collections Distribution",
    activityTitle: "Recent Activity",
    bars: ["Ptolemaic", "Roman", "Byzantine", "Islamic", "Coptic"],
    activity: [
      { title: "Golden Mask of Psusennes I",    desc: "Added to Vault C by Dr. Youssef",              time: "2 HOURS AGO",  status: "CATALOGED" },
      { title: "Attic Black-Figure Amphora",     desc: "Status updated to 'Needs Conservation'",       time: "5 HOURS AGO",  status: "FLAGGED"   },
      { title: "Marble Bust of Hadrian",         desc: "Loan approved for British Museum exhibition",  time: "1 DAY AGO",    status: "LOAN OUT"  },
    ],
  },
  ar: {
    pageTitle: "نظرة عامة على المقتنيات",
    pageSub: "ملخص شامل لمقاييس المجموعة الحالية وأنشطة الفهرسة الأخيرة.",
    totalArtifacts: "إجمالي القطع الأثرية",
    recentAcq: "الاقتناءات الأخيرة",
    recentAcqSub: "+٣ هذا الشهر",
    pending: "المراجعات المعلقة",
    pendingSub: "تتطلب اهتماماً",
    chartTitle: "توزيع المجموعات",
    activityTitle: "النشاط الأخير",
    bars: ["البطالمة", "الرومان", "البيزنطيون", "الإسلامية", "القبطية"],
    activity: [
      { title: "القناع الذهبي لبسوسينيس الأول", desc: "أضيف إلى الخزينة ج من قِبَل د. يوسف",          time: "منذ ساعتين",    status: "مُفهرَس"   },
      { title: "أمفورا الأشكال السوداء الأتيكية",  desc: "تم تحديث الحالة إلى 'بحاجة إلى ترميم'",      time: "منذ ٥ ساعات",   status: "مُعلَّم"   },
      { title: "تمثال الإمبراطور هادريان الرخامي", desc: "تمت الموافقة على الإعارة لمعرض المتحف البريطاني", time: "منذ يوم واحد", status: "معار"      },
    ],
  },
};

const statusColor: Record<string, string> = {
  CATALOGED: "text-[var(--color-primary-container)] border-[var(--color-primary-container)]/20 bg-[var(--color-primary-container)]/10",
  "مُفهرَس":   "text-[var(--color-primary-container)] border-[var(--color-primary-container)]/20 bg-[var(--color-primary-container)]/10",
  FLAGGED:    "text-[var(--color-error-container)] border-[var(--color-error-container)]/20 bg-[var(--color-error-container)]/10",
  "مُعلَّم":   "text-[var(--color-error-container)] border-[var(--color-error-container)]/20 bg-[var(--color-error-container)]/10",
  "LOAN OUT": "text-[var(--color-tertiary-container)] border-[var(--color-tertiary-container)]/20 bg-[var(--color-tertiary-container)]/10",
  "معار":     "text-[var(--color-tertiary-container)] border-[var(--color-tertiary-container)]/20 bg-[var(--color-tertiary-container)]/10",
};

const activityImages = [
  "https://lh3.googleusercontent.com/aida-public/AB6AXuA5Qws8Wy8F9m57HNlIzrq5GNpxIcnipOPFjn8yAqz9wm4K-rvr_o77Np6ck59P2YYI0kZsyjqoRyLID8oM7ByEtchmt_AxMi3XKKvVKSFyf0XqlAohafnYvkVuwkm_y2lhDt22ZHfO1nwzrLFi_hA7eLrpQSzOAnWenYgu0Y0bFFi-21bTFsNpM_7fw20rkurL_6dXIXFNFXqXC4K6-NL1_UPfYgot38inCtBQ2FK4_xZ5ZCVQk-BOKMeDrqgaZ1cQeeKqVMQ6rBw",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuBAc7Z7muIzl04BqXsP5yxD1EAnW0JI9wQ3hjAFBDV-IHlPOXQjYO_NSuzzAZ32uDtT0TUlvLSSFNdReNy8ds8ONRyPiQAypl7jzN2mR-x0fNaJhWxmIqKNS1CCn_XhEOa6qihkvRT8xErh4B58P7p8TQuaDP5ZKxjInEeilgA--sUZm9WvWskQBtzlz5qJmC7gHu1BZpqzVcXPZgxfQ2odYM_CWxDr5JE0zYnxo0zPAh3EyasZWCq8N6p9KCa56A5RfdBEPkeQzrE",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuAhHXJQ87CPZEeJP3viZuHVNdNcMF5prYqmCkkOtJ1guma5E5nCd3mBcvkwpBIN9knmnTSrKZl2I3x_qmDP5SjzrCdVW96jtZSthPeYYy5pY6w6a5lEun3XMHGqHl0fwGzdfCpgrdHYnmkurrrTcxBpg-MUtECKYifk4qNIEDNHkN9Plun72G-xhGCSpmXhhJWNkZL7Ox0OkpYQBFgzGU15F6z1V2uL4ePAzuMwUvKCpOV8eWWkjWqNVfaLsM2ANPHFJr_-uqwBaf4",
];

export default function AdminDashboard() {
  const { locale } = useAdminLocale();
  const isAr = locale === "ar";
  const t = L[isAr ? "ar" : "en"];

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
            <p className="font-[family-name:var(--font-display-lg)] text-6xl font-bold text-[var(--color-primary-container)]">1,240</p>
            <div className="w-12 h-[1px] bg-[var(--color-primary-container)] mt-6" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[rgba(26,24,37,0.8)] backdrop-blur border border-[var(--color-gold)]/20 p-6 flex flex-col justify-between shadow-inner">
              <h3 className={`${hFont(locale)} text-xs uppercase tracking-widest text-[var(--color-on-surface-variant)] mb-2`}>{t.recentAcq}</h3>
              <p className="font-[family-name:var(--font-headline-md)] text-3xl text-[var(--color-surface-tint)]">12</p>
              <p className={`text-xs text-[var(--color-on-surface-variant)] ${bodyFont(locale)} mt-2`}>{t.recentAcqSub}</p>
            </div>
            <div className="bg-[rgba(26,24,37,0.8)] backdrop-blur border border-[var(--color-gold)]/20 border-t-[var(--color-error-container)]/50 p-6 flex flex-col justify-between shadow-inner">
              <h3 className={`${hFont(locale)} text-xs uppercase tracking-widest text-[var(--color-on-surface-variant)] mb-2`}>{t.pending}</h3>
              <p className="font-[family-name:var(--font-headline-md)] text-3xl text-[var(--color-error-container)]">5</p>
              <p className={`text-xs text-[var(--color-on-surface-variant)] ${bodyFont(locale)} mt-2`}>{t.pendingSub}</p>
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
            {[
              { height: "80%" }, { height: "60%" }, { height: "40%" }, { height: "25%" }, { height: "15%" },
            ].map((bar, i) => (
              <div key={i} className="flex flex-col items-center gap-2 group w-full px-1">
                <div
                  className="w-full bg-[var(--color-primary-container)]/20 border border-[var(--color-primary-container)]/50 group-hover:bg-[var(--color-primary-container)]/40 transition-colors relative cursor-pointer"
                  style={{ height: bar.height }}
                >
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 font-[family-name:var(--font-label-sm)] text-[var(--color-primary-container)] transition-opacity text-xs">
                    {[450, 320, 210, 150, 110][i]}
                  </div>
                </div>
                <span className={`text-[10px] uppercase text-[var(--color-on-surface-variant)] hidden sm:block ${hFont(locale)}`}>
                  {t.bars[i]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="relative z-10">
        <h3 className={`${hFont(locale)} text-xs uppercase tracking-widest text-[var(--color-primary-container)] mb-6 flex items-center gap-2`}>
          <Clock size={16} /> {t.activityTitle}
        </h3>
        <div className="flex flex-col gap-4">
          {t.activity.map((item, i) => (
            <div key={i} className="bg-[rgba(26,24,37,0.8)] backdrop-blur border border-[var(--color-gold)]/20 p-4 flex items-center gap-5 hover:border-[var(--color-primary-container)]/50 transition-colors cursor-pointer group shadow-inner">
              <div className="w-16 h-16 border border-[var(--color-primary-container)]/30 p-1 shrink-0">
                <div className="relative w-full h-full grayscale group-hover:grayscale-0 transition-all duration-500">
                  <Image src={activityImages[i]} alt={item.title} fill className="object-cover" unoptimized />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className={`${hFont(locale)} text-lg text-[var(--color-on-surface)] truncate`}>{item.title}</h4>
                <p className={`${bodyFont(locale)} text-sm text-[var(--color-on-surface-variant)] truncate`}>{item.desc}</p>
              </div>
              <div className={`text-right hidden sm:block shrink-0`}>
                <p className={`${hFont(locale)} text-xs text-[var(--color-on-surface-variant)] uppercase tracking-widest`}>{item.time}</p>
                <span className={`inline-block mt-2 px-2 py-1 ${hFont(locale)} text-[10px] border tracking-wider uppercase ${statusColor[item.status] ?? ""}`}>
                  {item.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
