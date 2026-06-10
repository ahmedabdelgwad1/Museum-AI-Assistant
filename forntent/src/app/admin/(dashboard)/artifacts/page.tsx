"use client";
import Image from "next/image";
import Link from "next/link";
import { Edit, Trash2, ChevronLeft, ChevronRight, X, Upload, Loader2 } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { hFont, bodyFont, dir } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";
import { useEffect, useRef, useState } from "react";
import { deleteArtifact, getAdminArtifacts, updateArtifact, uploadImage, translateBatch } from "@/lib/api";

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
    editTitle: "Edit Artifact",
    editNameEn: "Name (English)",
    editNameAr: "Name (Arabic)",
    editDescEn: "Description (English)",
    editDescAr: "Description (Arabic)",
    editSecEn: "Section (English)",
    editSecAr: "Section (Arabic)",
    editImg: "Image URL",
    editSave: "Save Changes",
    editCancel: "Cancel",
    editSaving: "Saving...",
    editSuccess: "Saved successfully.",
    editError: "Could not save. Please try again.",
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
    editTitle: "تعديل القطعة",
    editNameEn: "الاسم (إنجليزي)",
    editNameAr: "الاسم (عربي)",
    editDescEn: "الوصف (إنجليزي)",
    editDescAr: "الوصف (عربي)",
    editSecEn: "القسم (إنجليزي)",
    editSecAr: "القسم (عربي)",
    editImg: "رابط الصورة",
    editSave: "حفظ التعديلات",
    editCancel: "إلغاء",
    editSaving: "جاري الحفظ...",
    editSuccess: "تم الحفظ بنجاح.",
    editError: "تعذر الحفظ. حاول مرة أخرى.",
  },
};

const DEFAULT_IMAGE = "https://lh3.googleusercontent.com/aida-public/AB6AXuBA6FlkSGl2M4zEEA3OinZ07qJmwBvRI3Hn1vCCQkuHrizJB7RXQSHITEhDZtz-cJYxOTFB2JLhP_LrTleyttObKZ6KrRxTraIylhVPE2Ck8npsNHYsErkYKZcNOTIioWhZdMH8oQ6n0MSUI3jYYOuaZPdhM_3fk-TpP-nVpaO3-RBlJkM7oq_36irpT5Ni1XBWhukCz4gqoCaYrwKHh2GeDktpARciMtqUeeuvozJUshuODSg2nvY0DC7m0tYG9pJIR_C2EMjpxlU";

type ArtifactMetadata = {
  artifact_name_en?: string;
  artifact_name_ar?: string;
  description_en?: string;
  description_ar?: string;
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
  descEn: string;
  descAr: string;
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

  // Holds all 30 fetched items; pagination is done client-side
  const [allArtifacts, setAllArtifacts] = useState<ArtifactTableItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | number | null>(null);

  // Edit modal state
  const [editingItem, setEditingItem] = useState<ArtifactTableItem | null>(null);
  const [editForm, setEditForm] = useState({ nameEn: "", nameAr: "", descEn: "", descAr: "", sectionEn: "", sectionAr: "", image: "" });
  const [editSaving, setEditSaving] = useState(false);
  const [editMsg, setEditMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [imgUploading, setImgUploading] = useState(false);
  const editFileRef = useRef<HTMLInputElement>(null);

  const [lastEdited, setLastEdited] = useState<{name: "ar"|"en"|null, desc: "ar"|"en"|null, section: "ar"|"en"|null}>({
    name: null,
    desc: null,
    section: null
  });

  const [isAutoFilling, setIsAutoFilling] = useState(false);

  const handleAutoFillEdit = async () => {
    const fieldsToTranslate = [];
    
    // Smart Overwrite Logic for Name
    if (!editForm.nameAr && editForm.nameEn) fieldsToTranslate.push({ field_id: "nameAr", source_text: editForm.nameEn, target_lang: "ar" as const });
    else if (!editForm.nameEn && editForm.nameAr) fieldsToTranslate.push({ field_id: "nameEn", source_text: editForm.nameAr, target_lang: "en" as const });
    else if (editForm.nameAr && editForm.nameEn && lastEdited.name) {
      if (lastEdited.name === "ar") fieldsToTranslate.push({ field_id: "nameEn", source_text: editForm.nameAr, target_lang: "en" as const });
      else fieldsToTranslate.push({ field_id: "nameAr", source_text: editForm.nameEn, target_lang: "ar" as const });
    }

    // Smart Overwrite Logic for Description
    if (!editForm.descAr && editForm.descEn) fieldsToTranslate.push({ field_id: "descAr", source_text: editForm.descEn, target_lang: "ar" as const });
    else if (!editForm.descEn && editForm.descAr) fieldsToTranslate.push({ field_id: "descEn", source_text: editForm.descAr, target_lang: "en" as const });
    else if (editForm.descAr && editForm.descEn && lastEdited.desc) {
      if (lastEdited.desc === "ar") fieldsToTranslate.push({ field_id: "descEn", source_text: editForm.descAr, target_lang: "en" as const });
      else fieldsToTranslate.push({ field_id: "descAr", source_text: editForm.descEn, target_lang: "ar" as const });
    }

    // Smart Overwrite Logic for Section
    if (!editForm.sectionAr && editForm.sectionEn) fieldsToTranslate.push({ field_id: "sectionAr", source_text: editForm.sectionEn, target_lang: "ar" as const });
    else if (!editForm.sectionEn && editForm.sectionAr) fieldsToTranslate.push({ field_id: "sectionEn", source_text: editForm.sectionAr, target_lang: "en" as const });
    else if (editForm.sectionAr && editForm.sectionEn && lastEdited.section) {
      if (lastEdited.section === "ar") fieldsToTranslate.push({ field_id: "sectionEn", source_text: editForm.sectionAr, target_lang: "en" as const });
      else fieldsToTranslate.push({ field_id: "sectionAr", source_text: editForm.sectionEn, target_lang: "ar" as const });
    }

    if (fieldsToTranslate.length === 0) {
      alert(isAr ? "جميع الحقول محدثة." : "All fields are up to date.");
      return;
    }

    setIsAutoFilling(true);
    try {
      const translations = await translateBatch(fieldsToTranslate);
      setEditForm(prev => ({
        ...prev,
        ...translations
      }));
    } catch (err) {
      alert("Auto-fill failed. Please try again.");
    } finally {
      setIsAutoFilling(false);
    }
  };

  // Pagination — 5 items per page, fetch all items for local filtering
  const [page, setPage] = useState(1);
  const ITEMS_PER_PAGE = 5;
  const MAX_ITEMS = 1000;

  useEffect(() => {
    async function fetchArtifacts() {
      setLoading(true);
      // Fetch up to 1000 items so local search and pagination work across the whole DB
      const { records } = await getAdminArtifacts(1, MAX_ITEMS);

      if (records) {
        const formatted = (records as ArtifactRow[]).map(row => {
          const meta = readMetadata(row.metadata);
          return {
            id: row.id,
            nameEn: meta?.artifact_name_en || "Unknown Artifact",
            nameAr: meta?.artifact_name_ar || "قطعة غير معروفة",
            descEn: meta?.description_en || "",
            descAr: meta?.description_ar || "",
            sectionEn: meta?.section_name_en || "Unknown Section",
            sectionAr: meta?.section_name_ar || "قسم غير معروف",
            date: row.created_at ? new Date(row.created_at).toLocaleDateString(isAr ? 'ar-EG' : 'en-GB') : "N/A",
            image: meta?.image_url || DEFAULT_IMAGE
          };
        });
        setAllArtifacts(formatted);
      }
      setLoading(false);
    }
    fetchArtifacts().catch((error) => {
      console.error("Failed to load artifacts from backend:", error);
      setAllArtifacts([]);
      setLoading(false);
    });
  }, [isAr]);

  // Filtering & Pagination
  const searchParams = useSearchParams();
  const searchQuery = (searchParams.get("q") || "").toLowerCase();
  
  const filteredArtifacts = allArtifacts.filter((item) => {
    if (!searchQuery) return true;
    return (
      item.nameEn.toLowerCase().includes(searchQuery) ||
      item.nameAr.toLowerCase().includes(searchQuery) ||
      item.sectionEn.toLowerCase().includes(searchQuery) ||
      item.sectionAr.toLowerCase().includes(searchQuery)
    );
  });

  const totalCount = filteredArtifacts.length;
  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);
  const startItem = totalCount === 0 ? 0 : (page - 1) * ITEMS_PER_PAGE + 1;
  const endItem = Math.min(page * ITEMS_PER_PAGE, totalCount);
  const artifacts = filteredArtifacts.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE);

  const handleDelete = async (item: ArtifactTableItem) => {
    if (!window.confirm(t.deleteConfirm)) return;

    setDeletingId(item.id);
    try {
      await deleteArtifact(item.id, item.image);
    } catch (error) {
      console.error("Failed to delete artifact from backend:", error);
      alert(`${t.deleteError}\n\nDetails: ${error instanceof Error ? error.message : String(error)}`);
      setDeletingId(null);
      return;
    }

    const nextAll = allArtifacts.filter((a) => a.id !== item.id);
    setAllArtifacts(nextAll);
    setDeletingId(null);

    // If current page becomes empty after delete, go back one page
    const newTotalPages = Math.ceil(nextAll.length / ITEMS_PER_PAGE);
    if (page > newTotalPages && page > 1) {
      setPage((current) => current - 1);
    }
  };

  const openEdit = (item: ArtifactTableItem) => {
    setEditingItem(item);
    setEditForm({ nameEn: item.nameEn, nameAr: item.nameAr, descEn: item.descEn, descAr: item.descAr, sectionEn: item.sectionEn, sectionAr: item.sectionAr, image: item.image });
    setLastEdited({ name: null, desc: null, section: null });
    setEditMsg(null);
  };

  const handleSaveEdit = async () => {
    if (!editingItem) return;
    setEditSaving(true);
    setEditMsg(null);
    try {
      await updateArtifact(editingItem.id, {
        artifact_name_en: editForm.nameEn,
        artifact_name_ar: editForm.nameAr,
        description_en: editForm.descEn,
        description_ar: editForm.descAr,
        section_name_en: editForm.sectionEn,
        section_name_ar: editForm.sectionAr,
        image_url: editForm.image,
      });
      // Update local state immediately — no reload needed
      setAllArtifacts(prev =>
        prev.map(a =>
          a.id === editingItem.id
            ? { ...a, nameEn: editForm.nameEn, nameAr: editForm.nameAr, descEn: editForm.descEn, descAr: editForm.descAr, sectionEn: editForm.sectionEn, sectionAr: editForm.sectionAr, image: editForm.image }
            : a
        )
      );
      setEditMsg({ type: "ok", text: t.editSuccess });
      setTimeout(() => setEditingItem(null), 900);
    } catch (err) {
      console.error(err);
      const errorMsg = err instanceof Error ? err.message : String(err);
      setEditMsg({ type: "err", text: `${t.editError} (${errorMsg})` });
    } finally {
      setEditSaving(false);
    }
  };

  const handleImgUpload = async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    setImgUploading(true);
    try {
      const url = await uploadImage(file);
      setEditForm(f => ({ ...f, image: url }));
    } catch (err) {
      alert("Image upload failed: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setImgUploading(false);
    }
  };

  return (
    <>
    <div dir={dir(locale)} className="pt-10 px-6 md:px-12 pb-24 max-w-[1280px] mx-auto w-full relative">
      {/* Canvas Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-4">
        <div>
          <p className={`${hFont(locale)} text-primary mb-2 opacity-80 uppercase tracking-widest text-xs`}>{t.label}</p>
          <h1 className={`${hFont(locale)} text-on-surface text-4xl`}>{t.title}</h1>
        </div>
        <Link
          href="/admin/artifacts/new"
          className={`border-2 border-primary text-primary px-8 py-3 uppercase ${hFont(locale)} tracking-widest text-xs hover:bg-primary hover:text-[#171308] transition-all duration-500 hover:shadow-[inset_0_0_20px_0_rgba(230,195,100,0.5)] whitespace-nowrap`}
        >
          {t.addBtn}
        </Link>
      </div>

      {/* Table */}
      <div className="bg-bg-card/90 backdrop-blur rounded-sm border-t border-primary/40 shadow-2xl overflow-hidden relative">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-high/50 border-b-2 border-primary/30">
                {[t.colThumb, t.colName, t.colSection, t.colDate, t.colActions].map((col, i) => (
                  <th
                    key={col}
                    className={`p-5 ${hFont(locale)} text-primary uppercase tracking-widest text-xs ${i === 0 ? "w-24" : ""} ${i === 4 ? "text-right" : ""}`}
                  >
                    {col} {i === 1 && <span className="opacity-40 text-[9px] ml-1">{t.colNameSub}</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className={`${bodyFont(locale)} text-on-surface`}>
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-10 text-center text-on-surface-variant">
                    {t.loading}
                  </td>
                </tr>
              ) : artifacts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-10 text-center text-on-surface-variant">
                    {t.noData}
                  </td>
                </tr>
              ) : (
                artifacts.map((item) => (
                  <tr key={item.id} className="border-b border-primary/20 hover:bg-surface-variant/30 transition-colors group">
                    <td className="p-5">
                      <div className="w-14 h-14 bg-surface p-1 border border-primary/30 relative shadow-inner">
                        <div className="relative w-full h-full grayscale opacity-90 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-500">
                          <Image src={item.image} alt={item.nameEn} fill className="object-cover" unoptimized />
                        </div>
                      </div>
                    </td>
                    <td className="p-5">
                      <div className="flex flex-col gap-1">
                        <span className={`text-base text-on-surface ${isAr ? "font-(family-name:--font-almarai)" : ""}`}>
                          {isAr ? item.nameAr : item.nameEn}
                        </span>
                        <span className={`text-sm text-on-surface-variant opacity-60 ${isAr ? "" : "font-(family-name:--font-almarai)"}`} dir={isAr ? "ltr" : "rtl"}>
                          {isAr ? item.nameEn : item.nameAr}
                        </span>
                      </div>
                    </td>
                    <td className={`p-5 text-on-surface-variant text-sm`}>{isAr ? item.sectionAr : item.sectionEn}</td>
                    <td className={`p-5 text-outline ${hFont(locale)} text-sm tracking-wider`}>{item.date}</td>
                    <td className="p-5 text-right">
                      <div className="flex justify-end gap-3 opacity-60 group-hover:opacity-100 transition-opacity">
                        <button
                          aria-label="Edit"
                          onClick={() => openEdit(item)}
                          className="p-2 hover:text-primary hover:bg-primary/10 rounded-full transition-colors"
                        >
                          <Edit size={18} />
                        </button>
                        <button
                          aria-label="Delete"
                          onClick={() => handleDelete(item)}
                          disabled={deletingId === item.id}
                          className="p-2 hover:text-error hover:bg-error/10 rounded-full transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
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
        <div className="border-t border-primary/20 px-6 py-4 bg-surface-container-low/50 flex flex-col sm:flex-row justify-between items-center gap-4">
          <span className={`${hFont(locale)} text-outline opacity-70 uppercase tracking-widest text-xs`}>
            {t.showing.replace("{start}", startItem.toString()).replace("{end}", endItem.toString()).replace("{total}", totalCount.toString())}
          </span>
          <div className="flex gap-1 items-center flex-wrap justify-center">
            {/* Prev */}
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1 px-2 border border-primary/30 text-primary hover:bg-primary/10 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
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
                  <span key={`ellipsis-${i}`} className={`px-2 text-outline opacity-50 ${hFont(locale)} text-sm select-none`}>…</span>
                ) : (
                  <button
                    key={p}
                    onClick={() => setPage(p as number)}
                    className={`min-w-[36px] h-9 px-2 border text-sm transition-colors ${hFont(locale)} ${
                      page === p
                        ? "border-primary bg-primary text-[#171308]"
                        : "border-primary/30 text-primary hover:bg-primary/10"
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
              className="p-1 px-2 border border-primary/30 text-primary hover:bg-primary/10 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            >
              {isAr ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
            </button>
          </div>
        </div>
      </div>
    </div>

      {/* ─── Edit Modal ─── */}
      {editingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setEditingItem(null)}>
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

          {/* Panel */}
          <div
            dir={dir(locale)}
            className="relative z-10 w-full max-w-lg bg-bg-card border border-primary/40 border-t-primary-container/60 shadow-2xl p-8"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex justify-between items-center mb-8 gap-4">
              <h2 className={`${hFont(locale)} text-xl text-primary-container`}>{t.editTitle}</h2>
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={handleAutoFillEdit}
                  disabled={isAutoFilling}
                  className="flex items-center gap-2 border border-primary/40 hover:bg-primary/10 text-primary px-3 py-1.5 disabled:opacity-40 transition-colors"
                  title={isAr ? "ترجمة تلقائية للبيانات الناقصة" : "Auto-fill missing translations"}
                >
                  {isAutoFilling ? <Loader2 className="w-3 h-3 animate-spin" /> : "✨"}
                  <span className={`${hFont(locale)} text-[9px] uppercase tracking-wider font-bold`}>
                    {isAr ? "ترجمة الحقول الفارغة" : "Auto-Fill Missing"}
                  </span>
                </button>
                <button onClick={() => setEditingItem(null)} className="text-on-surface-variant hover:text-primary transition-colors">
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Form fields */}
            <div className="flex flex-col gap-5 max-h-[60vh] overflow-y-auto px-4 -mx-4 custom-scrollbar">
              {/* Text fields */}
              {([
                { label: t.editNameEn, key: "nameEn", source: "nameAr", lang: "en", dir: "ltr", isTextarea: false },
                { label: t.editNameAr, key: "nameAr", source: "nameEn", lang: "ar", dir: "rtl", isTextarea: false },
                { label: t.editDescEn, key: "descEn", source: "descAr", lang: "en", dir: "ltr", isTextarea: true },
                { label: t.editDescAr, key: "descAr", source: "descEn", lang: "ar", dir: "rtl", isTextarea: true },
                { label: t.editSecEn,  key: "sectionEn", source: "sectionAr", lang: "en", dir: "ltr", isTextarea: false },
                { label: t.editSecAr,  key: "sectionAr", source: "sectionEn", lang: "ar", dir: "rtl", isTextarea: false },
              ] as { label: string; key: keyof typeof editForm; source: keyof typeof editForm; lang: "ar"|"en"; dir: string; isTextarea: boolean }[]).map(({ label, key, source, lang, dir: d, isTextarea }) => (
                <div key={key}>
                  <div className="flex justify-between items-center mb-2">
                    <label className={`block ${hFont(locale)} text-[10px] uppercase tracking-widest text-on-surface-variant`}>{label}</label>
                  </div>
                  {isTextarea ? (
                    <textarea
                      dir={d}
                      rows={3}
                      value={editForm[key]}
                      onChange={e => {
                        setEditForm(f => ({ ...f, [key]: e.target.value }));
                        setLastEdited(prev => ({ ...prev, [key.startsWith("name") ? "name" : key.startsWith("desc") ? "desc" : "section"]: lang }));
                      }}
                      className={`w-full bg-surface-container-high/50 border border-primary/30 focus:border-primary outline-none px-4 py-3 text-sm text-on-surface ${bodyFont(locale)} transition-colors resize-none`}
                    />
                  ) : (
                    <input
                      dir={d}
                      value={editForm[key]}
                      onChange={e => {
                        setEditForm(f => ({ ...f, [key]: e.target.value }));
                        setLastEdited(prev => ({ ...prev, [key.startsWith("name") ? "name" : key.startsWith("desc") ? "desc" : "section"]: lang }));
                      }}
                      className={`w-full bg-surface-container-high/50 border border-primary/30 focus:border-primary outline-none px-4 py-3 text-sm text-on-surface ${bodyFont(locale)} transition-colors`}
                    />
                  )}
                </div>
              ))}

              {/* Image field with upload button */}
              <div>
                <label className={`block ${hFont(locale)} text-[10px] uppercase tracking-widest text-on-surface-variant mb-2`}>{t.editImg}</label>
                <div className="flex gap-2 items-stretch">
                  {/* URL input */}
                  <input
                    dir="ltr"
                    value={editForm.image}
                    onChange={e => setEditForm(f => ({ ...f, image: e.target.value }))}
                    placeholder="https://..."
                    className={`flex-1 bg-surface-container-high/50 border border-primary/30 focus:border-primary outline-none px-4 py-3 text-sm text-on-surface ${bodyFont(locale)} transition-colors min-w-0`}
                  />
                  {/* Upload button */}
                  <button
                    type="button"
                    title={isAr ? "رفع صورة" : "Upload image"}
                    onClick={() => editFileRef.current?.click()}
                    disabled={imgUploading}
                    className="shrink-0 px-4 border border-primary/40 text-primary hover:bg-primary/10 transition-colors disabled:opacity-40 flex items-center gap-2"
                  >
                    {imgUploading
                      ? <Loader2 size={16} className="animate-spin" />
                      : <Upload size={16} />}
                    <span className={`${hFont(locale)} text-[10px] uppercase tracking-wider hidden sm:block`}>
                      {imgUploading ? (isAr ? "جاري..." : "...") : (isAr ? "رفع" : "Upload")}
                    </span>
                  </button>
                  {/* Hidden file input */}
                  <input
                    ref={editFileRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleImgUpload(f); }}
                  />
                </div>
                {/* Thumbnail preview */}
                {editForm.image && (
                  <div className="mt-3 w-16 h-16 border border-primary/30 relative overflow-hidden">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={editForm.image} alt="preview" className="w-full h-full object-cover" onError={e => (e.currentTarget.style.display = "none")} />
                  </div>
                )}
              </div>
            </div>


            {/* Feedback */}
            {editMsg && (
              <p className={`mt-5 text-sm ${bodyFont(locale)} ${
                editMsg.type === "ok" ? "text-green-400" : "text-error"
              }`}>{editMsg.text}</p>
            )}

            {/* Actions */}
            <div className={`flex gap-3 mt-8 ${isAr ? "flex-row-reverse" : ""}`}>
              <button
                onClick={handleSaveEdit}
                disabled={editSaving}
                className={`flex-1 py-3 uppercase ${hFont(locale)} tracking-widest text-xs bg-primary text-[#171308] hover:opacity-90 disabled:opacity-50 transition-opacity`}
              >
                {editSaving ? t.editSaving : t.editSave}
              </button>
              <button
                onClick={() => setEditingItem(null)}
                className={`px-6 py-3 uppercase ${hFont(locale)} tracking-widest text-xs border border-primary/40 text-primary hover:bg-primary/10 transition-colors`}
              >
                {t.editCancel}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
