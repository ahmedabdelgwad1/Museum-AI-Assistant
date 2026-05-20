"use client";
import { Info, PenTool, Camera, Loader2, Upload, CheckCircle2 } from "lucide-react";
import { getDictionary } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { createArtifact, getAdminArtifacts, uploadImage } from "@/lib/api";

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
  const arabicClass = isRTL ? "font-[family-name:var(--font-arabic)]" : "";
  const headingClass = isRTL
    ? "font-[family-name:var(--font-arabic)]"
    : "font-[family-name:var(--font-headline-md)]";

  const router = useRouter();
  const [loading, setLoading] = useState(false);
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

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const name = formData.get("artifact_name") as string;
    const category = formData.get("category") as string;
    const hall = formData.get("hall") as string;
    const desc = formData.get("description") as string;
    const imageUrl = (formData.get("image_url") as string) || uploadedUrl;
    const selectedSection = sections.find((section) => section.id === category);
    
    // Fallback image url
    const DEFAULT_IMAGE = "https://lh3.googleusercontent.com/aida-public/AB6AXuBA6FlkSGl2M4zEEA3OinZ07qJmwBvRI3Hn1vCCQkuHrizJB7RXQSHITEhDZtz-cJYxOTFB2JLhP_LrTleyttObKZ6KrRxTraIylhVPE2Ck8npsNHYsErkYKZcNOTIioWhZdMH8oQ6n0MSUI3jYYOuaZPdhM_3fk-TpP-nVpaO3-RBlJkM7oq_36irpT5Ni1XBWhukCz4gqoCaYrwKHh2GeDktpARciMtqUeeuvozJUshuODSg2nvY0DC7m0tYG9pJIR_C2EMjpxlU";

    try {
      await createArtifact({
      artifact_name_en: name,
      artifact_name_ar: name, 
        description_en: desc || "No description provided.",
        description_ar: desc || "No description provided.",
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
      <div className={`mb-10 flex justify-between items-end border-b border-[var(--color-outline-variant)]/30 pb-6`}>
        <div>
          <h2 className={`${headingClass} text-[var(--color-primary)] mb-2 text-base uppercase tracking-widest`}>
            {t.pageLabel}
          </h2>
          <h1 className={`${headingClass} text-[var(--color-on-surface)] text-3xl sm:text-4xl`}>
            {t.pageTitle}
          </h1>
        </div>
        <div className={`pb-2 hidden md:block ${isRTL ? "text-left" : "text-right"}`}>
          <p className={`${headingClass} text-[var(--color-outline)] tracking-widest mb-1 uppercase text-xs`}>
            {t.registryDate}
          </p>
          <p className={`${headingClass} text-[var(--color-surface-tint)] text-lg`}>{today}</p>
        </div>
      </div>

      {/* Form Grid */}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left / Main column */}
        <div className="lg:col-span-8 flex flex-col gap-8">

          {/* Basic Information */}
          <section className="bg-[#1a1825] p-8 border-t border-[var(--color-primary)]/20 shadow-md">
            <div className={`flex items-center mb-8 border-b border-[var(--color-outline-variant)]/20 pb-4 gap-3`}>
              <Info className="text-[var(--color-primary)] w-5 h-5 shrink-0" />
              <h3 className={`${headingClass} text-lg text-[var(--color-on-surface)] uppercase tracking-widest`}>
                {t.sectionBasic}
              </h3>
            </div>

            <div className="space-y-8">
              {/* Artifact Name */}
              <div className="relative group">
                <label
                  htmlFor="artifact_name"
                  className={`block ${headingClass} text-[var(--color-primary)] mb-2 opacity-80 group-focus-within:opacity-100 transition-opacity uppercase tracking-wider text-xs`}
                >
                  {t.nameLabel}
                </label>
                <input
                  type="text"
                  id="artifact_name"
                  name="artifact_name"
                  required
                  placeholder={t.namePlaceholder}
                  dir={isRTL ? "rtl" : "ltr"}
                  className={`w-full bg-transparent border-0 border-b border-[var(--color-primary)]/40 focus:border-[var(--color-primary)] focus:ring-0 px-0 py-2 text-[var(--color-on-surface)] text-xl placeholder:text-[var(--color-outline-variant)] focus:outline-none ${isRTL ? "font-[family-name:var(--font-arabic)] text-right" : "font-[family-name:var(--font-body-lg)]"}`}
                />
              </div>

              {/* Category */}
              <div className="relative group">
                <label
                  htmlFor="category"
                  className={`block ${headingClass} text-[var(--color-primary)] mb-2 opacity-80 group-focus-within:opacity-100 transition-opacity uppercase tracking-wider text-xs`}
                >
                  {t.categoryLabel}
                </label>
                <select
                  id="category"
                  name="category"
                  required
                  className={`w-full bg-transparent border-0 border-b border-[var(--color-primary)]/40 focus:border-[var(--color-primary)] focus:ring-0 px-0 py-2 text-[var(--color-on-surface)] text-lg focus:outline-none ${isRTL ? "font-[family-name:var(--font-arabic)]" : "font-[family-name:var(--font-body-lg)]"}`}
                >
                  <option value="" className="bg-[#1a1825]">{t.categoryDefault}</option>
                  {sections.length > 0 ? (
                    sections.map((section) => (
                      <option key={section.id} value={section.id} className="bg-[#1a1825]">
                        {isRTL ? section.nameAr : section.nameEn} ({section.count})
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="sculpture" className="bg-[#1a1825]">{t.cat1}</option>
                      <option value="jewelry" className="bg-[#1a1825]">{t.cat2}</option>
                      <option value="manuscript" className="bg-[#1a1825]">{t.cat3}</option>
                      <option value="pottery" className="bg-[#1a1825]">{t.cat4}</option>
                    </>
                  )}
                </select>
              </div>

              {/* Exhibition Hall */}
              <div className="relative group">
                <label
                  htmlFor="hall"
                  className={`block ${headingClass} text-[var(--color-primary)] mb-2 opacity-80 group-focus-within:opacity-100 transition-opacity uppercase tracking-wider text-xs`}
                >
                  {t.hallLabel}
                </label>
                <select
                  id="hall"
                  name="hall"
                  className={`w-full bg-transparent border-0 border-b border-[var(--color-primary)]/40 focus:border-[var(--color-primary)] focus:ring-0 px-0 py-2 text-[var(--color-on-surface)] text-lg focus:outline-none ${isRTL ? "font-[family-name:var(--font-arabic)]" : "font-[family-name:var(--font-body-lg)]"}`}
                >
                  <option value="" className="bg-[#1a1825]">{t.hallDefault}</option>
                  <option value="hall_a" className="bg-[#1a1825]">{t.hall1}</option>
                  <option value="hall_b" className="bg-[#1a1825]">{t.hall2}</option>
                  <option value="hall_c" className="bg-[#1a1825]">{t.hall3}</option>
                </select>
              </div>
            </div>
          </section>

          {/* Historical Record */}
          <section className="bg-[#1a1825] p-8 border-t border-[var(--color-primary)]/20 shadow-md">
            <div className={`flex items-center mb-6 border-b border-[var(--color-outline-variant)]/20 pb-4 gap-3`}>
              <PenTool className="text-[var(--color-primary)] w-5 h-5 shrink-0" />
              <h3 className={`${headingClass} text-lg text-[var(--color-on-surface)] uppercase tracking-widest`}>
                {t.sectionDetails}
              </h3>
            </div>

            <div className="relative group">
              <label
                htmlFor="description"
                className={`block ${headingClass} text-[var(--color-primary)] mb-4 opacity-80 group-focus-within:opacity-100 transition-opacity uppercase tracking-wider text-xs`}
              >
                {t.descLabel}
              </label>
              <textarea
                id="description"
                name="description"
                required
                rows={5}
                placeholder={t.descPlaceholder}
                dir={isRTL ? "rtl" : "ltr"}
                className={`w-full bg-[var(--color-surface-container-low)] border border-[var(--color-primary)]/20 focus:border-[var(--color-primary)]/60 text-[var(--color-on-surface)] text-lg p-4 focus:outline-none resize-none placeholder:text-[var(--color-outline-variant)] leading-relaxed ${isRTL ? "font-[family-name:var(--font-arabic)] text-right leading-loose" : "font-[family-name:var(--font-body-md)]"}`}
              />
            </div>
          </section>
        </div>

        {/* Right column: Media + Actions */}
        <div className="lg:col-span-4 flex flex-col gap-8">

          {/* Media Upload */}
          <section className="bg-[rgba(26,24,37,0.5)] backdrop-blur-md p-6 border border-[var(--color-primary)]/10 flex-1 flex flex-col shadow-md">
            <div className="flex items-center mb-4 border-b border-[var(--color-outline-variant)]/20 pb-4 gap-3">
              <Camera className="text-[var(--color-primary)] w-5 h-5 shrink-0" />
              <h3 className={`${headingClass} text-base text-[var(--color-on-surface)] uppercase tracking-widest`}>
                {t.sectionMedia}
              </h3>
            </div>
            <p className={`${isRTL ? "font-[family-name:var(--font-arabic)] text-sm" : "font-[family-name:var(--font-body-md)] text-sm"} text-[var(--color-on-surface-variant)] mb-5`}>
              {t.mediaHint}
            </p>

            <div className="relative group mb-5">
              <label
                htmlFor="image_url"
                className={`${headingClass} block text-[var(--color-primary)] mb-2 opacity-80 group-focus-within:opacity-100 transition-opacity uppercase tracking-wider text-xs`}
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
                className="w-full bg-transparent border-0 border-b border-[var(--color-primary)]/40 focus:border-[var(--color-primary)] focus:ring-0 px-0 py-2 text-[var(--color-on-surface)] text-sm placeholder:text-[var(--color-outline-variant)] focus:outline-none font-[family-name:var(--font-body-md)]"
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
              className="flex-1 min-h-[220px] border-2 border-dashed border-[var(--color-primary)]/40 hover:border-[var(--color-primary)] transition-colors bg-[var(--color-surface-container-lowest)]/30 flex flex-col items-center justify-center p-6 text-center cursor-pointer group relative overflow-hidden"
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
                      <Loader2 className="w-8 h-8 text-[var(--color-primary)] animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-8 h-8 text-green-400" />
                    )}
                    <span className={`${headingClass} text-xs uppercase tracking-widest text-[var(--color-primary)]`}>
                      {uploading
                        ? (isRTL ? "جاري الرفع..." : "Uploading...")
                        : (isRTL ? "تم الرفع — اضغط لتغيير" : "Uploaded — click to change")}
                    </span>
                  </div>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 rounded-full bg-[var(--color-primary)]/10 flex items-center justify-center mb-3 group-hover:bg-[var(--color-primary)]/20 transition-colors">
                    <Upload className="text-[var(--color-primary)] w-6 h-6" />
                  </div>
                  <span className={`${headingClass} text-[var(--color-primary)] text-xs uppercase tracking-widest mb-1 block`}>
                    {isRTL ? "اسحب الصورة هنا أو اضغط للاختيار" : "Drop image or click to browse"}
                  </span>
                  <span className={`${isRTL ? "font-[family-name:var(--font-arabic)] text-xs" : "font-[family-name:var(--font-body-md)] text-sm"} text-[var(--color-outline-variant)] block`}>
                    {t.uploadHint}
                  </span>
                  <span className="text-[var(--color-outline-variant)] text-[10px] mt-3 block uppercase tracking-wider">
                    {t.uploadTypes}
                  </span>
                </>
              )}
            </div>
          </section>

          {/* Submit Action */}
          <section className="bg-[#1a1825] p-6 border-t border-[var(--color-primary)] shadow-[inset_0_1px_0_rgba(232,201,122,0.2)]">
            <div className="mb-5">
              <label className={`flex items-start gap-3 cursor-pointer ${isRTL ? "flex-row-reverse" : ""}`}>
                <input
                  type="checkbox"
                  required
                  className="mt-1 w-4 h-4 text-[var(--color-primary)] bg-transparent border-[var(--color-primary)]/50 rounded-none shrink-0"
                />
                <span className={`${isRTL ? "font-[family-name:var(--font-arabic)] text-sm leading-loose" : "font-[family-name:var(--font-body-md)] text-sm"} text-[var(--color-on-surface-variant)]`}>
                  {t.certify}
                </span>
              </label>
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full relative group overflow-hidden border-2 border-[var(--color-primary)] text-[var(--color-primary)] px-8 py-4 uppercase tracking-[0.2em] transition-all duration-500 hover:text-[#0a0a0f] disabled:opacity-50 disabled:cursor-not-allowed bg-[var(--color-primary)]/5 ${headingClass} text-xs font-bold flex items-center justify-center`}
            >
              <span className="relative z-10 flex items-center gap-2">
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {t.submit}
              </span>
              <div className="absolute inset-0 bg-[var(--color-primary)] translate-y-[100%] group-hover:translate-y-0 transition-transform duration-300 ease-in-out z-0"></div>
            </button>
          </section>
        </div>
      </form>
    </div>
  );
}
