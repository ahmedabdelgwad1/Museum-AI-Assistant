"use client";
import Image from "next/image";
import Link from "next/link";
import { Edit, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { hFont, bodyFont, dir } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";
import { useEffect, useState } from "react";
import { deleteArtifact, getAdminArtifacts } from "@/lib/api";

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
    showing: "Showing {start} to {end} of {total} Entries",
    loading: "Loading artifacts...",
    noData: "No artifacts found.",
    deleteConfirm: "Delete this artifact from Supabase?",
    deleteError: "Could not delete artifact. Please check permissions.",
    editSoon: "Editing will be connected next."
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
    showing: "عرض {start} إلى {end} من {total} قطعة",
    loading: "جاري تحميل القطع...",
    noData: "لا توجد قطع أثرية.",
    deleteConfirm: "هل تريد حذف هذه القطعة من Supabase؟",
    deleteError: "تعذر حذف القطعة. راجع صلاحيات قاعدة البيانات.",
    editSoon: "سيتم ربط التعديل لاحقاً."
  },
};

const DEFAULT_IMAGE = "https://lh3.googleusercontent.com/aida-public/AB6AXuBA6FlkSGl2M4zEEA3OinZ07qJmwBvRI3Hn1vCCQkuHrizJB7RXQSHITEhDZtz-cJYxOTFB2JLhP_LrTleyttObKZ6KrRxTraIylhVPE2Ck8npsNHYsErkYKZcNOTIioWhZdMH8oQ6n0MSUI3jYYOuaZPdhM_3fk-TpP-nVpaO3-RBlJkM7oq_36irpT5Ni1XBWhukCz4gqoCaYrwKHh2GeDktpARciMtqUeeuvozJUshuODSg2nvY0DC7m0tYG9pJIR_C2EMjpxlU";

type ArtifactMetadata = {
  artifact_name_en?: string;
  artifact_name_ar?: string;
  section_name_en?: string;
  section_name_ar?: string;
  image_url?: string;
};

type ArtifactRow = {
  id: string | number;
  metadata: ArtifactMetadata | string | null;
  created_at: string | null;
};

type ArtifactTableItem = {
  id: string | number;
  nameEn: string;
  nameAr: string;
  sectionEn: string;
  sectionAr: string;
  date: string;
  image: string;
};

function readMetadata(metadata: ArtifactRow["metadata"]): ArtifactMetadata {
  if (!metadata) return {};
  if (typeof metadata !== "string") return metadata;

  try {
    return JSON.parse(metadata) as ArtifactMetadata;
  } catch {
    return {};
  }
}

export default function AdminArtifacts() {
  const { locale } = useAdminLocale();
  const isAr = locale === "ar";
  const t = L[isAr ? "ar" : "en"];

  const [artifacts, setArtifacts] = useState<ArtifactTableItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [deletingId, setDeletingId] = useState<string | number | null>(null);
  
  // Pagination
  const [page, setPage] = useState(1);
  const limit = 5;

  useEffect(() => {
    async function fetchArtifacts() {
      setLoading(true);
      const { total, records } = await getAdminArtifacts(page, limit);
      setTotalCount(total);
        
      if (records) {
        const formatted = (records as ArtifactRow[]).map(row => {
          const meta = readMetadata(row.metadata);
          return {
            id: row.id,
            nameEn: meta?.artifact_name_en || "Unknown Artifact",
            nameAr: meta?.artifact_name_ar || "قطعة غير معروفة",
            sectionEn: meta?.section_name_en || "Unknown Section",
            sectionAr: meta?.section_name_ar || "قسم غير معروف",
            date: row.created_at ? new Date(row.created_at).toLocaleDateString(isAr ? 'ar-EG' : 'en-GB') : "N/A",
            image: meta?.image_url || DEFAULT_IMAGE
          };
        });
        setArtifacts(formatted);
      }
      setLoading(false);
    }
    fetchArtifacts().catch((error) => {
      console.error("Failed to load artifacts from backend:", error);
      setArtifacts([]);
      setLoading(false);
    });
  }, [page, isAr]);

  const totalPages = Math.ceil(totalCount / limit);
  const startItem = totalCount === 0 ? 0 : (page - 1) * limit + 1;
  const endItem = Math.min(page * limit, totalCount);

  const handleDelete = async (id: string | number) => {
    if (!window.confirm(t.deleteConfirm)) return;

    setDeletingId(id);
    try {
      await deleteArtifact(id);
    } catch (error) {
      console.error("Failed to delete artifact from backend:", error);
      alert(t.deleteError);
      setDeletingId(null);
      return;
    }

    const nextArtifacts = artifacts.filter((item) => item.id !== id);
    setArtifacts(nextArtifacts);
    setTotalCount((current) => Math.max(0, current - 1));
    setDeletingId(null);

    if (nextArtifacts.length === 0 && page > 1) {
      setPage((current) => current - 1);
    }
  };

  return (
    <div dir={dir(locale)} className="pt-10 px-6 md:px-12 pb-24 max-w-[1280px] mx-auto w-full relative">
      {/* Canvas Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-4">
        <div>
          <p className={`${hFont(locale)} text-[var(--color-primary)] mb-2 opacity-80 uppercase tracking-widest text-xs`}>{t.label}</p>
          <h1 className={`${hFont(locale)} text-[var(--color-on-surface)] text-4xl`}>{t.title}</h1>
        </div>
        <Link
          href="/admin/artifacts/new"
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
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-10 text-center text-[var(--color-on-surface-variant)]">
                    {t.loading}
                  </td>
                </tr>
              ) : artifacts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-10 text-center text-[var(--color-on-surface-variant)]">
                    {t.noData}
                  </td>
                </tr>
              ) : (
                artifacts.map((item) => (
                  <tr key={item.id} className="border-b border-[var(--color-primary)]/20 hover:bg-[var(--color-surface-variant)]/30 transition-colors group">
                    <td className="p-5">
                      <div className="w-14 h-14 bg-[var(--color-surface)] p-1 border border-[var(--color-primary)]/30 relative shadow-inner">
                        <div className="relative w-full h-full grayscale opacity-90 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-500">
                          <Image src={item.image} alt={item.nameEn} fill className="object-cover" unoptimized />
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
                    <td className={`p-5 text-[var(--color-on-surface-variant)] text-sm`}>{isAr ? item.sectionAr : item.sectionEn}</td>
                    <td className={`p-5 text-[var(--color-outline)] ${hFont(locale)} text-sm tracking-wider`}>{item.date}</td>
                    <td className="p-5 text-right">
                      <div className="flex justify-end gap-3 opacity-60 group-hover:opacity-100 transition-opacity">
                        <button
                          aria-label="Edit"
                          onClick={() => alert(t.editSoon)}
                          className="p-2 hover:text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 rounded-full transition-colors"
                        >
                          <Edit size={18} />
                        </button>
                        <button
                          aria-label="Delete"
                          onClick={() => handleDelete(item.id)}
                          disabled={deletingId === item.id}
                          className="p-2 hover:text-[var(--color-error)] hover:bg-[var(--color-error)]/10 rounded-full transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="border-t border-[var(--color-primary)]/20 px-6 py-4 bg-[var(--color-surface-container-low)]/50 flex flex-col sm:flex-row justify-between items-center gap-4">
          <span className={`${hFont(locale)} text-[var(--color-outline)] opacity-70 uppercase tracking-widest text-xs`}>
            {t.showing.replace("{start}", startItem.toString()).replace("{end}", endItem.toString()).replace("{total}", totalCount.toString())}
          </span>
          <div className="flex gap-1 items-center flex-wrap justify-center">
            {/* Prev */}
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1 px-2 border border-[var(--color-primary)]/30 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            >
              {isAr ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            </button>

            {/* Page numbers */}
            {(() => {
              const pages: (number | "...")[] = [];
              if (totalPages <= 7) {
                for (let i = 1; i <= totalPages; i++) pages.push(i);
              } else {
                pages.push(1);
                if (page > 3) pages.push("...");
                for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.push(i);
                if (page < totalPages - 2) pages.push("...");
                pages.push(totalPages);
              }
              return pages.map((p, i) =>
                p === "..." ? (
                  <span key={`ellipsis-${i}`} className={`px-2 text-[var(--color-outline)] opacity-50 ${hFont(locale)} text-sm select-none`}>…</span>
                ) : (
                  <button
                    key={p}
                    onClick={() => setPage(p as number)}
                    className={`min-w-[36px] h-9 px-2 border text-sm transition-colors ${hFont(locale)} ${
                      page === p
                        ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-[#171308]"
                        : "border-[var(--color-primary)]/30 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10"
                    }`}
                  >
                    {p}
                  </button>
                )
              );
            })()}

            {/* Next */}
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages || totalPages === 0}
              className="p-1 px-2 border border-[var(--color-primary)]/30 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            >
              {isAr ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
