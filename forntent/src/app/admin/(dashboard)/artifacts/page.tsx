"use client";
import Image from "next/image";
import Link from "next/link";
import { Edit, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { getDictionary, hFont, bodyFont, dir } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";

const L = {
  en: {
    label: "Registry System",
    title: "Curated Collection",
    addBtn: "Add New Artifact",
    colThumb: "Thumbnail",
    colName: "Artifact Name",
    colNameSub: "(EN/AR)",
    colSection: "Section",
    colDate: "Date Added",
    colActions: "Actions",
    showing: "Showing 1 to 4 of 1,248 Entries",
    artifacts: [
      { nameEn: "Rosetta Stone Fragment",  nameAr: "حجر رشيد (جزء)",             section: "Ptolemaic Period",           date: "1802.04.15" },
      { nameEn: "Mask of Tutankhamun",     nameAr: "قناع توت عنخ آمون",          section: "New Kingdom, 18th Dynasty",  date: "1925.11.28" },
      { nameEn: "Bust of Nefertiti",       nameAr: "تمثال نفرتيتي",              section: "Amarna Period",              date: "1912.12.06" },
      { nameEn: "Alabaster Canopic Jars",  nameAr: "أواني كانوبية من المرمر",    section: "Middle Kingdom",             date: "1895.03.12" },
    ],
  },
  ar: {
    label: "نظام السجل",
    title: "المجموعة المقتناة",
    addBtn: "إضافة قطعة جديدة",
    colThumb: "الصورة المصغرة",
    colName: "اسم القطعة",
    colNameSub: "(ع/EN)",
    colSection: "القسم",
    colDate: "تاريخ الإضافة",
    colActions: "الإجراءات",
    showing: "عرض ١ إلى ٤ من ١٬٢٤٨ قطعة",
    artifacts: [
      { nameEn: "Rosetta Stone Fragment",  nameAr: "حجر رشيد (جزء)",             section: "العصر البطلمي",              date: "١٨٠٢.٠٤.١٥" },
      { nameEn: "Mask of Tutankhamun",     nameAr: "قناع توت عنخ آمون",          section: "المملكة الحديثة، الأسرة ١٨", date: "١٩٢٥.١١.٢٨" },
      { nameEn: "Bust of Nefertiti",       nameAr: "تمثال نفرتيتي",              section: "عصر العمارنة",               date: "١٩١٢.١٢.٠٦" },
      { nameEn: "Alabaster Canopic Jars",  nameAr: "أواني كانوبية من المرمر",    section: "المملكة الوسطى",             date: "١٨٩٥.٠٣.١٢" },
    ],
  },
};

const IMAGES = [
  "https://lh3.googleusercontent.com/aida-public/AB6AXuBA6FlkSGl2M4zEEA3OinZ07qJmwBvRI3Hn1vCCQkuHrizJB7RXQSHITEhDZtz-cJYxOTFB2JLhP_LrTleyttObKZ6KrRxTraIylhVPE2Ck8npsNHYsErkYKZcNOTIioWhZdMH8oQ6n0MSUI3jYYOuaZPdhM_3fk-TpP-nVpaO3-RBlJkM7oq_36irpT5Ni1XBWhukCz4gqoCaYrwKHh2GeDktpARciMtqUeeuvozJUshuODSg2nvY0DC7m0tYG9pJIR_C2EMjpxlU",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuDSV75_oln4uJaSTUFvYqeJYK3N66WZfYGpDQTTU6FM9RrhKt9P_TZqQW3Za9XBb8ix68tejUlGnqkJNzmIaotAfjhskVqVbRMMYSqym2WQo8U0jbPXwDd0zkhhxe6UdfC-xboIvOK9s8m8d12FaUtfMBKmMlRD_oAFEBB1I6TBnOb_uBVtRxfuVaXfsp4m8V8ajqSsRi-hOJwbdxQWVBQlQ71hjL96c-FDe_CIIPSeIENnRRbXm_rdqrniS8ztWjgqhqeS3h88E-E",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuCpQiFQmYJHbbA96Ig7clfMKWlFrLMMiNyOyfDpfOMamkznTAVOyS7QxuEqULO05AT4pqDbfQAyh0XDb4I7VVnC0JP78cDQ7ICHRwePslKsGgJ8RR3nnHh4qr-Qs6ZOVAJTPv0vH8gnegq98Qfw1TAYW2-PS8_5zdf_oIGYRciNLLRqYH7-siNAWMDohsDQEaL5AblmkA6izmrkX8Dl-fiKkw2XFn6lAJO3L-lYQJehMs0bVFUT0iILL6rn2JsIz6GFj7EcJnovsWU",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuCEDOytbZTS1GRIL-RWmak3ZGLkyavfnKrURvOAb-uwisBDY4QqsCtQYqI30weSB1RWX8T442CQTRaLRLLQ_LtY_1a9VNxcrDNvX8mNmHebVDDcJqcztGQgWR7xIZGsTZAVMXVvhcmauCYoTWyiULBayuYqsUi33hhk2s5f0atJhJjocJ33VycjCpjj3aQez4VplP1Ej18iv6ZlzQm6KpDJZNdC_oVgFj0rF0am_2KFvFsODl1w1_QN_PjBoI2AuuNcWk8ISy46Tg8",
];

export default function AdminArtifacts() {
  const { locale } = useAdminLocale();
  const isAr = locale === "ar";
  const t = L[isAr ? "ar" : "en"];

  return (
    <div dir={dir(locale)} className="pt-10 px-6 md:px-12 pb-24 max-w-[1280px] mx-auto w-full relative">
      {/* Canvas Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-4">
        <div>
          <p className={`${hFont(locale)} text-[var(--color-primary)] mb-2 opacity-80 uppercase tracking-widest text-xs`}>{t.label}</p>
          <h1 className={`${hFont(locale)} text-[var(--color-on-surface)] text-4xl`}>{t.title}</h1>
        </div>
        <Link
          href="new"
          className={`border-2 border-[var(--color-primary)] text-[var(--color-primary)] px-8 py-3 uppercase ${hFont(locale)} tracking-widest text-xs hover:bg-[var(--color-primary)] hover:text-[#171308] transition-all duration-500 hover:shadow-[inset_0_0_20px_0_rgba(230,195,100,0.5)] whitespace-nowrap`}
        >
          {t.addBtn}
        </Link>
      </div>

      {/* Table */}
      <div className="bg-[#1a1825]/90 backdrop-blur rounded-sm border-t border-[var(--color-primary)]/40 shadow-2xl overflow-hidden relative">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--color-surface-container-high)]/50 border-b-2 border-[var(--color-primary)]/30">
                {[t.colThumb, t.colName, t.colSection, t.colDate, t.colActions].map((col, i) => (
                  <th
                    key={col}
                    className={`p-5 ${hFont(locale)} text-[var(--color-primary)] uppercase tracking-widest text-xs ${i === 0 ? "w-24" : ""} ${i === 4 ? "text-right" : ""}`}
                  >
                    {col} {i === 1 && <span className="opacity-40 text-[9px] ml-1">{t.colNameSub}</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className={`${bodyFont(locale)} text-[var(--color-on-surface)]`}>
              {t.artifacts.map((item, i) => (
                <tr key={i} className="border-b border-[var(--color-primary)]/20 hover:bg-[var(--color-surface-variant)]/30 transition-colors group">
                  <td className="p-5">
                    <div className="w-14 h-14 bg-[var(--color-surface)] p-1 border border-[var(--color-primary)]/30 relative shadow-inner">
                      <div className="relative w-full h-full grayscale opacity-90 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-500">
                        <Image src={IMAGES[i]} alt={item.nameEn} fill className="object-cover" unoptimized />
                      </div>
                    </div>
                  </td>
                  <td className="p-5">
                    <div className="flex flex-col gap-1">
                      <span className={`text-base text-[var(--color-on-surface)] ${isAr ? "font-[family-name:var(--font-arabic)]" : ""}`}>
                        {isAr ? item.nameAr : item.nameEn}
                      </span>
                      <span className={`text-sm text-[var(--color-on-surface-variant)] opacity-60 ${isAr ? "" : "font-[family-name:var(--font-arabic)]"}`} dir={isAr ? "ltr" : "rtl"}>
                        {isAr ? item.nameEn : item.nameAr}
                      </span>
                    </div>
                  </td>
                  <td className={`p-5 text-[var(--color-on-surface-variant)] text-sm`}>{item.section}</td>
                  <td className={`p-5 text-[var(--color-outline)] ${hFont(locale)} text-sm tracking-wider`}>{item.date}</td>
                  <td className="p-5 text-right">
                    <div className="flex justify-end gap-3 opacity-60 group-hover:opacity-100 transition-opacity">
                      <button aria-label="Edit" className="p-2 hover:text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 rounded-full transition-colors">
                        <Edit size={18} />
                      </button>
                      <button aria-label="Delete" className="p-2 hover:text-[var(--color-error)] hover:bg-[var(--color-error)]/10 rounded-full transition-colors">
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="border-t border-[var(--color-primary)]/20 px-6 py-4 bg-[var(--color-surface-container-low)]/50 flex justify-between items-center">
          <span className={`${hFont(locale)} text-[var(--color-outline)] opacity-70 uppercase tracking-widest text-xs hidden sm:block`}>{t.showing}</span>
          <div className="flex gap-2">
            <button className="p-1 border border-[var(--color-primary)]/30 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 transition-colors">
              {isAr ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
            </button>
            <button className="p-1 border border-[var(--color-primary)] text-[var(--color-background)] bg-[var(--color-primary)] transition-colors">
              <span className="font-[family-name:var(--font-headline-md)] px-2 text-sm">1</span>
            </button>
            <button className="p-1 border border-[var(--color-primary)]/30 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 transition-colors">
              <span className="font-[family-name:var(--font-headline-md)] px-2 text-sm">2</span>
            </button>
            <button className="p-1 border border-[var(--color-primary)]/30 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 transition-colors">
              {isAr ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
