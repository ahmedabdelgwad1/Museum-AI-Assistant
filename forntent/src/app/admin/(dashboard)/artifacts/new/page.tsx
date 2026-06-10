"use client";
import { Info, PenTool, Camera, Loader2, Upload, CheckCircle2 } from "lucide-react";
import { getDictionary } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { createArtifact, getAdminArtifacts, uploadImage, translateBatch } from "@/lib/api";

type ArtifactMetadata = {
  section_number?: string | number;
  section_name_en?: string;
  section_name_ar?: string;
};

type SectionOption = {
  id: string;
  nameEn: string;
  nameAr: string;
  count: number;
};

function readMetadata(metadata: ArtifactMetadata | string | null): ArtifactMetadata {
  if (!metadata) return {};
  if (typeof metadata !== "string") return metadata;

  try {
    return JSON.parse(metadata) as ArtifactMetadata;
  } catch {
    return {};
  }
}

export default function AdminNewArtifact() {
  const { locale } = useAdminLocale();
  const t = getDictionary(locale as "en" | "ar").admin.new;
  const isRTL = locale === "ar";
  const arabicClass = isRTL ? "font-(family-name:--font-almarai)" : "";
  const headingClass = isRTL
    ? "font-(family-name:--font-almarai)"
    : "font-(family-name:--font-headline-md)";

  const router = useRouter();
  const [loading, setLoading] = useState(false);
  
  // Controlled fields for bi-directional translation
  const [nameAr, setNameAr] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [descAr, setDescAr] = useState("");
  const [descEn, setDescEn] = useState("");
  
  // Track last edited language per field to enable smart overwriting
  const [lastEdited, setLastEdited] = useState<{name: "ar"|"en"|null, desc: "ar"|"en"|null}>({
    name: null,
    desc: null
  });
  
  // Translation state
  const [isAutoFilling, setIsAutoFilling] = useState(false);
  const [sections, setSections] = useState<SectionOption[]>([]);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedUrl, setUploadedUrl] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageUrlInputRef = useRef<HTMLInputElement>(null);

  // Today's date for registry
  const today = new Date().toLocaleDateString((locale as string) === "ar" ? "ar-EG" : "en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  useEffect(() => {
    async function fetchSections() {
      const { records } = await getAdminArtifacts(1, 1000);

      const sectionMap = new Map<string, SectionOption>();

      records?.forEach((row) => {
        const meta = readMetadata(row.metadata);
        const sectionId = meta.section_number?.toString().trim();

        if (!sectionId || sectionId.toLowerCase() === "nan") return;

        const existing = sectionMap.get(sectionId);
        if (existing) {
          existing.count += 1;
          return;
        }

        sectionMap.set(sectionId, {
          id: sectionId,
          nameEn: meta.section_name_en || `Section ${sectionId}`,
          nameAr: meta.section_name_ar || `قسم ${sectionId}`,
          count: 1,
        });
      });

      setSections(
        Array.from(sectionMap.values()).sort((a, b) =>
          a.id.localeCompare(b.id, undefined, { numeric: true })
        )
      );
    }

    fetchSections().catch((error) => {
      console.error("Failed to load sections from backend:", error);
    });
  }, []);

  const handleFileSelect = async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    // Show local preview immediately
    setImagePreview(URL.createObjectURL(file));
    setUploading(true);
    try {
      const url = await uploadImage(file);
      setUploadedUrl(url);
      // Auto-fill the image_url input
      if (imageUrlInputRef.current) imageUrlInputRef.current.value = url;
    } catch (err) {
      alert("Image upload failed: " + (err instanceof Error ? err.message : String(err)));
      setImagePreview(null);
    } finally {
      setUploading(false);
    }
  };

  const handleAutoFill = async () => {
    const fieldsToTranslate = [];
    
    // Smart Overwrite Logic for Name
    if (nameAr && !nameEn) fieldsToTranslate.push({ field_id: "nameEn", source_text: nameAr, target_lang: "en" as const });
    else if (!nameAr && nameEn) fieldsToTranslate.push({ field_id: "nameAr", source_text: nameEn, target_lang: "ar" as const });
    else if (nameAr && nameEn && lastEdited.name) {
      if (lastEdited.name === "ar") fieldsToTranslate.push({ field_id: "nameEn", source_text: nameAr, target_lang: "en" as const });
      else fieldsToTranslate.push({ field_id: "nameAr", source_text: nameEn, target_lang: "ar" as const });
    }

    // Smart Overwrite Logic for Description
    if (descAr && !descEn) fieldsToTranslate.push({ field_id: "descEn", source_text: descAr, target_lang: "en" as const });
    else if (!descAr && descEn) fieldsToTranslate.push({ field_id: "descAr", source_text: descEn, target_lang: "ar" as const });
    else if (descAr && descEn && lastEdited.desc) {
      if (lastEdited.desc === "ar") fieldsToTranslate.push({ field_id: "descEn", source_text: descAr, target_lang: "en" as const });
      else fieldsToTranslate.push({ field_id: "descAr", source_text: descEn, target_lang: "ar" as const });
    }

    if (fieldsToTranslate.length === 0) {
      alert(isRTL ? "جميع الحقول محدثة." : "All fields are up to date.");
      return;
    }

    setIsAutoFilling(true);
    try {
      const translations = await translateBatch(fieldsToTranslate);
      if (translations.nameAr) setNameAr(translations.nameAr);
      if (translations.nameEn) setNameEn(translations.nameEn);
      if (translations.descAr) setDescAr(translations.descAr);
      if (translations.descEn) setDescEn(translations.descEn);
    } catch (err) {
      alert("Auto-fill failed. Please try again.");
    } finally {
      setIsAutoFilling(false);
    }
  };

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const category = formData.get("category") as string;
    const hall = formData.get("hall") as string;
    const imageUrl = (formData.get("image_url") as string) || uploadedUrl;
    const selectedSection = sections.find((section) => section.id === category);
    
    // Fallback image url
    const DEFAULT_IMAGE = "https://lh3.googleusercontent.com/aida-public/AB6AXuBA6FlkSGl2M4zEEA3OinZ07qJmwBvRI3Hn1vCCQkuHrizJB7RXQSHITEhDZtz-cJYxOTFB2JLhP_LrTleyttObKZ6KrRxTraIylhVPE2Ck8npsNHYsErkYKZcNOTIioWhZdMH8oQ6n0MSUI3jYYOuaZPdhM_3fk-TpP-nVpaO3-RBlJkM7oq_36irpT5Ni1XBWhukCz4gqoCaYrwKHh2GeDktpARciMtqUeeuvozJUshuODSg2nvY0DC7m0tYG9pJIR_C2EMjpxlU";

    try {
      await createArtifact({
        artifact_name_en: nameEn || "Unknown",
        artifact_name_ar: nameAr || "Unknown", 
        description_en: descEn || "No description provided.",
        description_ar: descAr || "No description provided.",
        section_number: selectedSection?.id || category || "",
        section_name_en: selectedSection?.nameEn || category || "Unknown",
        section_name_ar: selectedSection?.nameAr || category || "Unknown",
        hall_en: hall,
        hall_ar: hall,
        image_url: imageUrl?.trim() || DEFAULT_IMAGE
      });
      router.push("/admin/artifacts");
    } catch (error) {
      alert("Error saving artifact: " + (error instanceof Error ? error.message : String(error)));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      dir={isRTL ? "rtl" : "ltr"}
      className={`flex-1 w-full max-w-[1100px] mx-auto px-6 pt-10 pb-24 ${arabicClass}`}
    >
      {/* Page Header */}
      <div className={`mb-10 flex justify-between items-end border-b border-outline-variant/30 pb-6`}>
        <div>
          <h2 className={`${headingClass} text-primary mb-2 text-base uppercase tracking-widest`}>
            {t.pageLabel}
          </h2>
          <h1 className={`${headingClass} text-on-surface text-3xl sm:text-4xl`}>
            {t.pageTitle}
          </h1>
        </div>
        <div className={`pb-2 hidden md:block ${isRTL ? "text-left" : "text-right"}`}>
          <p className={`${headingClass} text-outline tracking-widest mb-1 uppercase text-xs`}>
            {t.registryDate}
          </p>
          <p className={`${headingClass} text-surface-tint text-lg`}>{today}</p>
        </div>
      </div>

      {/* Form Grid */}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left / Main column */}
        <div className="lg:col-span-8 flex flex-col gap-8">

          {/* Basic Information */}
          <section className="bg-bg-card p-8 border-t border-primary/20 shadow-md">
            <div className={`flex items-center justify-between mb-8 border-b border-outline-variant/20 pb-4`}>
              <div className="flex items-center gap-3">
                <Info className="text-primary w-5 h-5 shrink-0" />
                <h3 className={`${headingClass} text-lg text-on-surface uppercase tracking-widest`}>
                  {t.sectionBasic}
                </h3>
              </div>
              
              <button
                type="button"
                onClick={handleAutoFill}
                disabled={isAutoFilling}
                className="flex items-center gap-2 border border-primary/40 hover:bg-primary/10 text-primary px-4 py-2 disabled:opacity-40 transition-colors"
                title={isRTL ? "ترجمة تلقائية للبيانات الناقصة" : "Auto-fill missing translations"}
              >
                {isAutoFilling ? <Loader2 className="w-4 h-4 animate-spin" /> : "✨"}
                <span className={`${headingClass} text-[10px] sm:text-xs uppercase tracking-wider font-bold`}>
                  {isRTL ? "ترجمة الحقول الفارغة" : "Auto-Fill Missing"}
                </span>
              </button>
            </div>

            <div className="space-y-8">
              {/* Artifact Name (Arabic) */}
              <div className="relative group bg-surface-container-low p-4 border border-primary/20 rounded-md">
                <div className="flex justify-between items-center mb-2">
                  <label
                    htmlFor="artifact_name_ar"
                    className={`block ${headingClass} text-primary opacity-80 uppercase tracking-wider text-xs`}
                  >
                    اسم القطعة (عربي)
                  </label>
                </div>
                <input
                  type="text"
                  id="artifact_name_ar"
                  name="artifact_name_ar"
                  required
                  value={nameAr}
                  onChange={(e) => {
                    setNameAr(e.target.value);
                    setLastEdited(prev => ({...prev, name: "ar"}));
                  }}
                  placeholder={isRTL ? t.namePlaceholder : "مثال: تمثال أبو الهول"}
                  dir="rtl"
                  className={`w-full bg-transparent border-0 border-b border-primary/40 focus:border-primary focus:ring-0 px-0 py-2 text-on-surface text-xl placeholder:text-outline-variant focus:outline-none font-(family-name:--font-almarai) text-right`}
                />
              </div>

              {/* Artifact Name (English) */}
              <div className="relative group bg-surface-container-low p-4 border border-primary/20 rounded-md">
                <div className="flex justify-between items-center mb-2">
                  <label
                    htmlFor="artifact_name_en"
                    className={`block ${headingClass} text-primary opacity-80 uppercase tracking-wider text-xs`}
                  >
                    Artifact Name (English)
                  </label>
                </div>
                <input
                  type="text"
                  id="artifact_name_en"
                  name="artifact_name_en"
                  required
                  value={nameEn}
                  onChange={(e) => {
                    setNameEn(e.target.value);
                    setLastEdited(prev => ({...prev, name: "en"}));
                  }}
                  placeholder="e.g. The Great Sphinx"
                  dir="ltr"
                  className={`w-full bg-transparent border-0 border-b border-primary/40 focus:border-primary focus:ring-0 px-0 py-2 text-on-surface text-xl placeholder:text-outline-variant focus:outline-none font-(family-name:--font-body-lg) text-left`}
                />
              </div>

              {/* Category */}
              <div className="relative group">
                <label
                  htmlFor="category"
                  className={`block ${headingClass} text-primary mb-2 opacity-80 group-focus-within:opacity-100 transition-opacity uppercase tracking-wider text-xs`}
                >
                  {t.categoryLabel}
                </label>
                <select
                  id="category"
                  name="category"
                  required
                  className={`w-full bg-transparent border-0 border-b border-primary/40 focus:border-primary focus:ring-0 px-0 py-2 text-on-surface text-lg focus:outline-none ${isRTL ? "font-(family-name:--font-almarai)" : "font-(family-name:--font-body-lg)"}`}
                >
                  <option value="" className="bg-bg-card">{t.categoryDefault}</option>
                  {sections.length > 0 ? (
                    sections.map((section) => (
                      <option key={section.id} value={section.id} className="bg-bg-card">
                        {isRTL ? section.nameAr : section.nameEn} ({section.count})
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="sculpture" className="bg-bg-card">{t.cat1}</option>
                      <option value="jewelry" className="bg-bg-card">{t.cat2}</option>
                      <option value="manuscript" className="bg-bg-card">{t.cat3}</option>
                      <option value="pottery" className="bg-bg-card">{t.cat4}</option>
                    </>
                  )}
                </select>
              </div>

              {/* Exhibition Hall */}
              <div className="relative group">
                <label
                  htmlFor="hall"
                  className={`block ${headingClass} text-primary mb-2 opacity-80 group-focus-within:opacity-100 transition-opacity uppercase tracking-wider text-xs`}
                >
                  {t.hallLabel}
                </label>
                <select
                  id="hall"
                  name="hall"
                  className={`w-full bg-transparent border-0 border-b border-primary/40 focus:border-primary focus:ring-0 px-0 py-2 text-on-surface text-lg focus:outline-none ${isRTL ? "font-(family-name:--font-almarai)" : "font-(family-name:--font-body-lg)"}`}
                >
                  <option value="" className="bg-bg-card">{t.hallDefault}</option>
                  <option value="hall_a" className="bg-bg-card">{t.hall1}</option>
                  <option value="hall_b" className="bg-bg-card">{t.hall2}</option>
                  <option value="hall_c" className="bg-bg-card">{t.hall3}</option>
                </select>
              </div>
            </div>
          </section>

          {/* Historical Record */}
          <section className="bg-bg-card p-8 border-t border-primary/20 shadow-md">
            <div className={`flex items-center mb-6 border-b border-outline-variant/20 pb-4 gap-3`}>
              <PenTool className="text-primary w-5 h-5 shrink-0" />
              <h3 className={`${headingClass} text-lg text-on-surface uppercase tracking-widest`}>
                {t.sectionDetails}
              </h3>
            </div>

            {/* Description (Arabic) */}
            <div className="relative group bg-surface-container-low p-4 border border-primary/20 rounded-md mb-6">
              <div className="flex justify-between items-center mb-4">
                <label
                  htmlFor="description_ar"
                  className={`block ${headingClass} text-primary opacity-80 uppercase tracking-wider text-xs`}
                >
                  وصف القطعة (عربي)
                </label>
              </div>
              <textarea
                id="description_ar"
                name="description_ar"
                required
                rows={4}
                value={descAr}
                onChange={(e) => {
                  setDescAr(e.target.value);
                  setLastEdited(prev => ({...prev, desc: "ar"}));
                }}
                placeholder="اكتب وصفاً مفصلاً للقطعة هنا..."
                dir="rtl"
                className={`w-full bg-surface-container-lowest/50 border border-primary/20 focus:border-primary/60 text-on-surface text-lg p-4 focus:outline-none resize-none placeholder:text-outline-variant leading-loose font-(family-name:--font-almarai) text-right`}
              />
            </div>

            {/* Description (English) */}
            <div className="relative group bg-surface-container-low p-4 border border-primary/20 rounded-md">
              <div className="flex justify-between items-center mb-4">
                <label
                  htmlFor="description_en"
                  className={`block ${headingClass} text-primary opacity-80 uppercase tracking-wider text-xs`}
                >
                  Description (English)
                </label>
              </div>
              <textarea
                id="description_en"
                name="description_en"
                required
                rows={4}
                value={descEn}
                onChange={(e) => {
                  setDescEn(e.target.value);
                  setLastEdited(prev => ({...prev, desc: "en"}));
                }}
                placeholder="Write a detailed description here..."
                dir="ltr"
                className={`w-full bg-surface-container-lowest/50 border border-primary/20 focus:border-primary/60 text-on-surface text-lg p-4 focus:outline-none resize-none placeholder:text-outline-variant leading-relaxed font-(family-name:--font-body-md) text-left`}
              />
            </div>
          </section>
        </div>

        {/* Right column: Media + Actions */}
        <div className="lg:col-span-4 flex flex-col gap-8">

          {/* Media Upload */}
          <section className="bg-[rgba(26,24,37,0.5)] backdrop-blur-md p-6 border border-primary/10 flex-1 flex flex-col shadow-md">
            <div className="flex items-center mb-4 border-b border-outline-variant/20 pb-4 gap-3">
              <Camera className="text-primary w-5 h-5 shrink-0" />
              <h3 className={`${headingClass} text-base text-on-surface uppercase tracking-widest`}>
                {t.sectionMedia}
              </h3>
            </div>
            <p className={`${isRTL ? "font-(family-name:--font-almarai) text-sm" : "font-(family-name:--font-body-md) text-sm"} text-on-surface-variant mb-5`}>
              {t.mediaHint}
            </p>

            <div className="relative group mb-5">
              <label
                htmlFor="image_url"
                className={`${headingClass} block text-primary mb-2 opacity-80 group-focus-within:opacity-100 transition-opacity uppercase tracking-wider text-xs`}
              >
                {isRTL ? "رابط الصورة" : "Image URL"}
              </label>
              <input
                ref={imageUrlInputRef}
                type="url"
                id="image_url"
                name="image_url"
                dir="ltr"
                placeholder="https://..."
                className="w-full bg-transparent border-0 border-b border-primary/40 focus:border-primary focus:ring-0 px-0 py-2 text-on-surface text-sm placeholder:text-outline-variant focus:outline-none font-(family-name:--font-body-md)"
              />
            </div>

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }}
            />

            {/* Dropzone */}
            <div
              className="flex-1 min-h-[220px] border-2 border-dashed border-primary/40 hover:border-primary transition-colors bg-surface-container-lowest/30 flex flex-col items-center justify-center p-6 text-center cursor-pointer group relative overflow-hidden"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={e => e.preventDefault()}
              onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFileSelect(f); }}
            >
              {/* Image preview */}
              {imagePreview ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={imagePreview} alt="preview" className="absolute inset-0 w-full h-full object-cover opacity-40" />
                  <div className="relative z-10 flex flex-col items-center gap-2">
                    {uploading ? (
                      <Loader2 className="w-8 h-8 text-primary animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-8 h-8 text-green-400" />
                    )}
                    <span className={`${headingClass} text-xs uppercase tracking-widest text-primary`}>
                      {uploading
                        ? (isRTL ? "جاري الرفع..." : "Uploading...")
                        : (isRTL ? "تم الرفع — اضغط لتغيير" : "Uploaded — click to change")}
                    </span>
                  </div>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3 group-hover:bg-primary/20 transition-colors">
                    <Upload className="text-primary w-6 h-6" />
                  </div>
                  <span className={`${headingClass} text-primary text-xs uppercase tracking-widest mb-1 block`}>
                    {isRTL ? "اسحب الصورة هنا أو اضغط للاختيار" : "Drop image or click to browse"}
                  </span>
                  <span className={`${isRTL ? "font-(family-name:--font-almarai) text-xs" : "font-(family-name:--font-body-md) text-sm"} text-outline-variant block`}>
                    {t.uploadHint}
                  </span>
                  <span className="text-outline-variant text-[10px] mt-3 block uppercase tracking-wider">
                    {t.uploadTypes}
                  </span>
                </>
              )}
            </div>
          </section>

          {/* Submit Action */}
          <section className="bg-bg-card p-6 border-t border-primary shadow-[inset_0_1px_0_rgba(232,201,122,0.2)]">
            <div className="mb-5">
              <label className={`flex items-start gap-3 cursor-pointer ${isRTL ? "flex-row-reverse" : ""}`}>
                <input
                  type="checkbox"
                  required
                  className="mt-1 w-4 h-4 text-primary bg-transparent border-primary/50 rounded-none shrink-0"
                />
                <span className={`${isRTL ? "font-(family-name:--font-almarai) text-sm leading-loose" : "font-(family-name:--font-body-md) text-sm"} text-on-surface-variant`}>
                  {t.certify}
                </span>
              </label>
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full relative group overflow-hidden border-2 border-primary text-primary px-8 py-4 uppercase tracking-[0.2em] transition-all duration-500 hover:text-bg-primary disabled:opacity-50 disabled:cursor-not-allowed bg-primary/5 ${headingClass} text-xs font-bold flex items-center justify-center`}
            >
              <span className="relative z-10 flex items-center gap-2">
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {t.submit}
              </span>
              <div className="absolute inset-0 bg-primary translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-in-out z-0"></div>
            </button>
          </section>
        </div>
      </form>
    </div>
  );
}
