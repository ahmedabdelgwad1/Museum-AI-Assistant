"use client";
import Image from "next/image";
import { User, Settings as Tune, Shield, Camera, Check, Key, QrCode, LogOut } from "lucide-react";
import { getDictionary } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";

export default function AdminSettings() {
  const { locale, setLocale } = useAdminLocale();
  const isRTL = locale === "ar";
  const hClass = isRTL
    ? "font-[family-name:var(--font-arabic)]"
    : "font-[family-name:var(--font-headline-md)]";
  const bodyClass = isRTL
    ? "font-[family-name:var(--font-arabic)]"
    : "font-[family-name:var(--font-body-md)]";

  // Inline bilingual labels — settings page has lots of static copy
  const labels = {
    pageTitle:     isRTL ? "الإعدادات"                                        : "Settings",
    pageSubtitle:  isRTL ? "أدر ملفك الشخصي وبروتوكولات الأمان وتفضيلات النظام لبوابة أرشيف الإسكندرية." : "Manage your curatorial profile, security protocols, and system preferences for the Alexandria Archive portal.",
    sProfile:      isRTL ? "هوية الملف الشخصي"                               : "Profile Identity",
    changePortrait: isRTL ? "تغيير الصورة الشخصية"                            : "Change Portrait",
    fullName:      isRTL ? "الاسم الكامل"                                     : "Full Name",
    email:         isRTL ? "البريد المؤسسي"                                   : "Institutional Email",
    title:         isRTL ? "اللقب والمسمى الوظيفي"                           : "Title & Designation",
    titleNote:     isRTL ? "تعديل اللقب يتطلب موافقة مجلس الأرشيف."          : "Title modifications require archivist board approval.",
    saveBtn:       isRTL ? "حفظ التعديلات"                                   : "Save Modifications",
    sSystem:       isRTL ? "معاملات النظام"                                   : "System Parameters",
    langLabel:     isRTL ? "لغة الواجهة"                                     : "Interface Language",
    dispatchLabel: isRTL ? "إعدادات الإشعارات"                               : "Dispatch Settings",
    acqAlert:      isRTL ? "تنبيهات الاقتناء"                                : "Acquisition Alerts",
    acqAlertSub:   isRTL ? "استلام رسائل عند فهرسة قطع جديدة."               : "Receive missives when new artifacts are cataloged.",
    scholarDigest: isRTL ? "ملخصات طلبات الباحثين"                           : "Scholar Request Digests",
    scholarDigestSub: isRTL ? "ملخص يومي لطلبات الوصول إلى الأرشيف."         : "Daily summary of archive access petitions.",
    sysAnomalies:  isRTL ? "شذوذات النظام"                                   : "System Anomalies",
    sysAnomaliesSub: isRTL ? "إشعار فوري بأي انحراف في التحكم المناخي أو الأمني." : "Immediate notification of climate control or security deviations.",
    sSecurity:     isRTL ? "بروتوكول الأمان"                                 : "Security Protocol",
    currentCipher: isRTL ? "الرمز الحالي"                                    : "Current Cipher",
    newCipher:     isRTL ? "الرمز الجديد"                                    : "New Cipher",
    confirmCipher: isRTL ? "تأكيد الرمز الجديد"                             : "Confirm New Cipher",
    updateCipher:  isRTL ? "تحديث الرمز"                                     : "Update Cipher",
    twoFA:         isRTL ? "المصادقة الثنائية"                               : "Two-Factor Authentication",
    twoFASub:      isRTL ? "اطلب رمز تحقق ثانوياً عند الوصول من موقع غير معروف." : "Require a secondary verification codex when accessing the archive from an unknown location.",
    recoveryRunes: isRTL ? "توليد رموز الاسترداد"                            : "Generate Recovery Runes",
    terminateSessions: isRTL ? "إنهاء جميع الجلسات النشطة"                  : "Terminate All Active Sessions",
  };

  return (
    <div
      dir={isRTL ? "rtl" : "ltr"}
      className={`flex-1 w-full max-w-[1280px] mx-auto px-6 pt-10 pb-24 relative overflow-hidden ${isRTL ? "font-[family-name:var(--font-arabic)]" : ""}`}
    >
      {/* Atmospheric glow */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-[var(--color-primary)]/5 rounded-full blur-[120px] -z-10 translate-x-1/3 -translate-y-1/3 pointer-events-none" />

      {/* Page Header */}
      <header className="mb-12">
        <h2 className={`${hClass} text-4xl sm:text-5xl text-[var(--color-primary)] opacity-90 mb-4`}>
          {labels.pageTitle}
        </h2>
        <p className={`${bodyClass} text-lg text-[var(--color-on-surface-variant)] max-w-2xl`}>
          {labels.pageSubtitle}
        </p>
      </header>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start relative z-10">

        {/* Left Column */}
        <div className="xl:col-span-7 flex flex-col gap-8">

          {/* Profile Card */}
          <section className="bg-[#1a1825]/80 backdrop-blur-md border-t border-[var(--color-primary)]/30 p-8 sm:p-10 relative overflow-hidden group shadow-2xl">
            <div className="absolute inset-0 border border-[var(--color-primary)]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            <div className="flex items-center gap-4 mb-10 border-b border-[var(--color-outline-variant)] pb-6">
              <User className="text-[var(--color-primary)] w-7 h-7 shrink-0" />
              <h3 className={`${hClass} text-2xl sm:text-3xl text-[var(--color-on-surface)]`}>{labels.sProfile}</h3>
            </div>

            <div className="flex flex-col md:flex-row gap-10 items-start">
              {/* Avatar */}
              <div className="flex flex-col items-center gap-4 shrink-0">
                <div className="w-28 h-28 rounded-sm border border-[var(--color-primary)]/40 overflow-hidden relative group-hover:border-[var(--color-primary)]/80 transition-colors duration-500">
                  <div className="w-full h-full relative">
                    <Image
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuDzYuJ6hUzolr_Q1K-CezVYQOTU_jFbIuWX4TRtlgLV-vbr30MUooF7uBnleG4b1kX89T_OeOEKCb77O3kU_1PTJXdx8RJymw3WmsCmCe3Fx0kuCZkV3H0i3LPvXBY-rErnzApgiCTpfWYo1TsRmQYhul0aKXWU0B1gKvuGXv1AKzEINP9PBVgYetZNHvOwmQCE7d1eVQRdyaODYHXZ_81ZMiEJptroaAEWD06N7bw5S5rpUi8kJfbQxsvmCUxL7TaxNW8lLAvwqU4"
                      alt="Curator Profile"
                      fill
                      className="object-cover sepia-[.3] contrast-125"
                      unoptimized
                    />
                  </div>
                  <div className="absolute inset-0 bg-[var(--color-background)]/60 opacity-0 hover:opacity-100 transition-opacity duration-300 flex items-center justify-center cursor-pointer">
                    <Camera className="text-[var(--color-primary)] w-7 h-7" />
                  </div>
                </div>
                <button className={`${hClass} text-xs text-[var(--color-primary)]/70 hover:text-[var(--color-primary)] transition-colors tracking-widest uppercase`}>
                  {labels.changePortrait}
                </button>
              </div>

              {/* Form */}
              <form className="flex-1 w-full space-y-8 mt-6 md:mt-0">
                {[
                  { id: "full_name", label: labels.fullName, type: "text",  value: isRTL ? "د. إلياس ثورن" : "Dr. Elias Thorne",                     readOnly: false },
                  { id: "inst_email", label: labels.email, type: "email", value: "e.thorne@alexandria-archive.org",                                    readOnly: false },
                  { id: "job_title", label: labels.title, type: "text",  value: isRTL ? "كبير أمناء المتحف" : "Chief Curator of Antiquities",          readOnly: true  },
                ].map(({ id, label, type, value, readOnly }) => (
                  <div key={id} className="relative group">
                    <label
                      htmlFor={id}
                      className={`block ${hClass} text-xs text-[var(--color-primary)]/60 uppercase tracking-widest mb-2 group-focus-within:text-[var(--color-primary)] transition-colors`}
                    >
                      {label}
                    </label>
                    <input
                      id={id}
                      type={type}
                      defaultValue={value}
                      readOnly={readOnly}
                      dir={isRTL ? "rtl" : "ltr"}
                      className={`w-full bg-transparent border-0 border-b border-[var(--color-outline-variant)] focus:border-[var(--color-primary)] focus:ring-0 px-0 py-2 text-xl text-[var(--color-on-surface)] transition-colors outline-none ${readOnly ? "opacity-60 cursor-not-allowed" : ""} ${isRTL ? "font-[family-name:var(--font-arabic)] text-right" : "font-[family-name:var(--font-body-lg)]"}`}
                    />
                    {readOnly && (
                      <p className={`text-xs text-[var(--color-on-surface-variant)]/50 mt-2 ${bodyClass} italic`}>{labels.titleNote}</p>
                    )}
                  </div>
                ))}
                <div className="pt-2">
                  <button type="button" className={`border-2 border-[var(--color-primary)] text-[var(--color-primary)] ${hClass} text-xs uppercase tracking-widest px-8 py-3 hover:bg-[var(--color-primary)] hover:text-[#0a0a0f] transition-all duration-300`}>
                    {labels.saveBtn}
                  </button>
                </div>
              </form>
            </div>
          </section>

          {/* System Preferences */}
          <section className="bg-[#1a1825]/80 backdrop-blur-md border-t border-[var(--color-primary)]/30 p-8 sm:p-10 relative overflow-hidden shadow-2xl">
            <div className="flex items-center gap-4 mb-8 border-b border-[var(--color-outline-variant)] pb-6">
              <Tune className="text-[var(--color-primary)] w-7 h-7 shrink-0" />
              <h3 className={`${hClass} text-2xl sm:text-3xl text-[var(--color-on-surface)]`}>{labels.sSystem}</h3>
            </div>

            <div className="space-y-10">
              {/* Language toggle */}
              <div>
                <h4 className={`${hClass} text-xs text-[var(--color-primary)]/80 uppercase tracking-widest mb-4`}>{labels.langLabel}</h4>
                <div className="flex flex-wrap items-center gap-4">
                  <button onClick={() => setLocale("en")} className={`border px-6 py-2 ${hClass} text-xs uppercase tracking-widest transition-colors ${ locale === "en" ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10 text-[var(--color-primary)]" : "border-[var(--color-outline-variant)] text-[var(--color-on-surface-variant)] hover:border-[var(--color-primary)]/50 hover:text-[var(--color-primary)]" }`}>EN - English</button>
                  <button onClick={() => setLocale("ar")} className={`border px-6 py-2 font-[family-name:var(--font-arabic)] text-xl transition-colors ${ locale === "ar" ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10 text-[var(--color-primary)]" : "border-[var(--color-outline-variant)] text-[var(--color-on-surface-variant)] hover:border-[var(--color-primary)]/50 hover:text-[var(--color-primary)]" }`}>عربي</button>
                </div>
              </div>

              {/* Notifications */}
              <div>
                <h4 className={`${hClass} text-xs text-[var(--color-primary)]/80 uppercase tracking-widest mb-6`}>{labels.dispatchLabel}</h4>
                <div className="space-y-6">
                  {[
                    { label: labels.acqAlert,      sub: labels.acqAlertSub,      checked: true  },
                    { label: labels.scholarDigest,  sub: labels.scholarDigestSub, checked: true  },
                    { label: labels.sysAnomalies,  sub: labels.sysAnomaliesSub,  checked: false },
                  ].map(({ label, sub, checked }) => (
                    <label key={label} className={`flex items-start gap-4 cursor-pointer group/chk ${isRTL ? "flex-row-reverse" : ""}`}>
                      <div className="relative flex items-center justify-center mt-1 shrink-0">
                        <input type="checkbox" defaultChecked={checked} className="peer sr-only" />
                        <div className="w-5 h-5 border border-[var(--color-outline-variant)] peer-checked:border-[var(--color-primary)] peer-checked:bg-[var(--color-primary)] transition-all rounded-sm flex items-center justify-center">
                          <Check className="text-[#0a0a0f] w-3 h-3 opacity-0 peer-checked:opacity-100 transition-opacity" strokeWidth={4} />
                        </div>
                      </div>
                      <div className={isRTL ? "text-right" : ""}>
                        <p className={`${bodyClass} text-xl text-[var(--color-on-surface)] group-hover/chk:text-[var(--color-primary)] transition-colors`}>{label}</p>
                        <p className={`${bodyClass} text-sm text-[var(--color-on-surface-variant)]/60 mt-1`}>{sub}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Right Column: Security */}
        <div className="xl:col-span-5">
          <section className="bg-[#1a1825]/80 backdrop-blur-md border-t border-[var(--color-primary)]/30 p-8 sm:p-10 relative overflow-hidden shadow-2xl flex flex-col h-full">
            <div className="flex items-center gap-4 mb-10 border-b border-[var(--color-outline-variant)] pb-6 shrink-0">
              <Shield className="text-[var(--color-primary)] w-7 h-7 shrink-0" />
              <h3 className={`${hClass} text-2xl sm:text-3xl text-[var(--color-on-surface)]`}>{labels.sSecurity}</h3>
            </div>

            <form className="space-y-8 flex-1 flex flex-col">
              <div className="space-y-8">
                {[labels.currentCipher, labels.newCipher, labels.confirmCipher].map((lbl, i) => (
                  <div key={i} className="relative group mt-6 first:mt-0">
                    <label className={`block ${hClass} text-xs text-[var(--color-primary)]/60 uppercase tracking-widest absolute -top-5 ${isRTL ? "right-0" : "left-0"} group-focus-within:text-[var(--color-primary)] transition-colors`}>
                      {lbl}
                    </label>
                    <input
                      type="password"
                      placeholder="••••••••"
                      dir="ltr"
                      className="w-full bg-transparent border-0 border-b border-[var(--color-outline-variant)] focus:border-[var(--color-primary)] focus:ring-0 px-0 py-2 font-[family-name:var(--font-body-lg)] text-xl text-[var(--color-on-surface)] tracking-widest transition-colors outline-none"
                    />
                  </div>
                ))}
                <button type="button" className={`border border-[var(--color-outline-variant)] text-[var(--color-on-surface-variant)] ${hClass} text-xs uppercase tracking-widest px-6 py-2 hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-all duration-300`}>
                  {labels.updateCipher}
                </button>
              </div>

              {/* Divider */}
              <div className="flex items-center gap-4 py-4 opacity-50">
                <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-[var(--color-primary)] to-transparent" />
                <Key className="text-[var(--color-primary)] w-4 h-4" />
                <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent via-[var(--color-primary)] to-transparent" />
              </div>

              {/* 2FA */}
              <div className="flex-1">
                <div className={`flex justify-between items-start gap-4 mb-4 ${isRTL ? "flex-row-reverse" : ""}`}>
                  <div className={isRTL ? "text-right" : ""}>
                    <h4 className={`${hClass} text-xs text-[var(--color-primary)]/80 uppercase tracking-widest mb-2`}>{labels.twoFA}</h4>
                    <p className={`${bodyClass} text-sm text-[var(--color-on-surface-variant)]/80`}>{labels.twoFASub}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer shrink-0 mt-1">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-[var(--color-surface-variant)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[var(--color-on-surface)] after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-primary)] border border-[var(--color-outline-variant)]" />
                  </label>
                </div>
                <button type="button" className={`text-[var(--color-primary)] ${hClass} text-xs uppercase tracking-widest flex items-center gap-2 hover:opacity-80 transition-opacity mt-4 ${isRTL ? "flex-row-reverse" : ""}`}>
                  <QrCode className="w-5 h-5" /> {labels.recoveryRunes}
                </button>
              </div>

              {/* Terminate sessions */}
              <div className="pt-6 border-t border-[var(--color-outline-variant)]/30 mt-auto">
                <button type="button" className={`w-full border border-[var(--color-error)]/50 text-[var(--color-error)]/80 ${hClass} text-xs uppercase tracking-widest px-6 py-4 hover:bg-[var(--color-error)]/10 hover:text-[var(--color-error)] hover:border-[var(--color-error)] transition-all duration-300 flex items-center justify-center gap-3`}>
                  <LogOut className="w-5 h-5" /> {labels.terminateSessions}
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
