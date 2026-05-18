"use client";
import { Info, PenTool, Camera } from "lucide-react";
import { getDictionary } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";

export default function AdminNewArtifact() {
  const { locale } = useAdminLocale();
  const t = getDictionary(locale as "en" | "ar").admin.new;
  const isRTL = locale === "ar";
  const arabicClass = isRTL ? "font-[family-name:var(--font-arabic)]" : "";
  const headingClass = isRTL
    ? "font-[family-name:var(--font-arabic)]"
    : "font-[family-name:var(--font-headline-md)]";

  // Today's date for registry
  const today = new Date().toLocaleDateString((locale as string) === "ar" ? "ar-EG" : "en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

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
      <form className="grid grid-cols-1 lg:grid-cols-12 gap-8">
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
                  className={`w-full bg-transparent border-0 border-b border-[var(--color-primary)]/40 focus:border-[var(--color-primary)] focus:ring-0 px-0 py-2 text-[var(--color-on-surface)] text-lg focus:outline-none ${isRTL ? "font-[family-name:var(--font-arabic)]" : "font-[family-name:var(--font-body-lg)]"}`}
                >
                  <option value="" className="bg-[#1a1825]">{t.categoryDefault}</option>
                  <option value="sculpture" className="bg-[#1a1825]">{t.cat1}</option>
                  <option value="jewelry" className="bg-[#1a1825]">{t.cat2}</option>
                  <option value="manuscript" className="bg-[#1a1825]">{t.cat3}</option>
                  <option value="pottery" className="bg-[#1a1825]">{t.cat4}</option>
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

            {/* Dropzone */}
            <div className="flex-1 min-h-[220px] border-2 border-dashed border-[var(--color-primary)]/40 hover:border-[var(--color-primary)] transition-colors bg-[var(--color-surface-container-lowest)]/30 flex flex-col items-center justify-center p-6 text-center cursor-pointer group">
              <div className="w-12 h-12 rounded-full bg-[var(--color-primary)]/10 flex items-center justify-center mb-3 group-hover:bg-[var(--color-primary)]/20 transition-colors">
                <Camera className="text-[var(--color-primary)] w-6 h-6" />
              </div>
              <span className={`${headingClass} text-[var(--color-primary)] text-xs uppercase tracking-widest mb-1 block`}>
                {t.uploadLabel}
              </span>
              <span className={`${isRTL ? "font-[family-name:var(--font-arabic)] text-xs" : "font-[family-name:var(--font-body-md)] text-sm"} text-[var(--color-outline-variant)] block`}>
                {t.uploadHint}
              </span>
              <span className="text-[var(--color-outline-variant)] text-[10px] mt-3 block uppercase tracking-wider">
                {t.uploadTypes}
              </span>
            </div>
          </section>

          {/* Submit Action */}
          <section className="bg-[#1a1825] p-6 border-t border-[var(--color-primary)] shadow-[inset_0_1px_0_rgba(232,201,122,0.2)]">
            <div className="mb-5">
              <label className={`flex items-start gap-3 cursor-pointer ${isRTL ? "flex-row-reverse" : ""}`}>
                <input
                  type="checkbox"
                  className="mt-1 w-4 h-4 text-[var(--color-primary)] bg-transparent border-[var(--color-primary)]/50 rounded-none shrink-0"
                />
                <span className={`${isRTL ? "font-[family-name:var(--font-arabic)] text-sm leading-loose" : "font-[family-name:var(--font-body-md)] text-sm"} text-[var(--color-on-surface-variant)]`}>
                  {t.certify}
                </span>
              </label>
            </div>
            <button
              type="submit"
              className={`w-full relative group overflow-hidden border-2 border-[var(--color-primary)] text-[var(--color-primary)] px-8 py-4 uppercase tracking-[0.2em] transition-all duration-500 hover:text-[#0a0a0f] bg-[var(--color-primary)]/5 ${headingClass} text-xs font-bold`}
            >
              <span className="relative z-10">{t.submit}</span>
              <div className="absolute inset-0 bg-[var(--color-primary)] translate-y-[100%] group-hover:translate-y-0 transition-transform duration-300 ease-in-out z-0"></div>
            </button>
          </section>
        </div>
      </form>
    </div>
  );
}
