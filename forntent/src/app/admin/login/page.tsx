"use client";
import { Eye } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getDictionary, hFont, dir } from "@/lib/dictionaries";

const L = {
  en: {
    title: "Bibliotheca\nAlexandrina",
    sub: "Antiquities Registry",
    emailLabel: "Museum Email",
    emailPlaceholder: "scholar@alexandrina.gov.eg",
    passLabel: "Security Key",
    submit: "Enter Sanctuary",
    requestAccess: "Request Archival Access",
  },
  ar: {
    title: "مكتبة\nالإسكندرية",
    sub: "سجل الآثار",
    emailLabel: "البريد المؤسسي",
    emailPlaceholder: "scholar@alexandrina.gov.eg",
    passLabel: "مفتاح الأمان",
    submit: "الدخول إلى الملاذ",
    requestAccess: "طلب صلاحية الوصول",
  },
};

export default function AdminLogin() {
  const locale: "en" | "ar" = "en"; // Default admin language
  const isAr = (locale as string) === "ar";
  const t = L[isAr ? "ar" : "en"];
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    router.push(`/admin`);
  };

  return (
    <div
      dir={dir(locale)}
      className="bg-[var(--color-background)] min-h-screen flex items-center justify-center relative overflow-hidden text-[var(--color-on-surface)]"
    >
      <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_center,_var(--color-surface-variant)_0%,_var(--color-background)_60%)] opacity-40 pointer-events-none" />

      <main className="relative z-10 w-full max-w-[480px] mx-4 p-12 bg-[var(--color-surface-container)]/80 backdrop-blur-[20px] border-t border-[var(--color-primary)]/20 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.8)]">
        {/* Header */}
        <header className="flex flex-col items-center justify-center mb-12 text-center">
          <Eye className="text-[var(--color-primary)] w-12 h-12 mb-6 opacity-90 stroke-1" />
          <h1 className={`${hFont(locale)} text-3xl text-[var(--color-on-surface)] mb-3 tracking-widest uppercase leading-tight whitespace-pre-line`}>
            {t.title}
          </h1>
          <p className={`${hFont(locale)} text-xs text-[var(--color-primary)] tracking-[0.3em] uppercase opacity-80`}>
            {t.sub}
          </p>
        </header>

        {/* Form */}
        <form onSubmit={handleLogin} className="flex flex-col gap-8">
          <div className="relative group">
            <label
              htmlFor="email"
              className={`block ${hFont(locale)} text-xs text-[var(--color-on-surface-variant)] mb-2 group-focus-within:text-[var(--color-primary)] uppercase tracking-wider transition-colors`}
            >
              {t.emailLabel}
            </label>
            <input
              type="email"
              id="email"
              name="email"
              placeholder={t.emailPlaceholder}
              required
              dir="ltr"
              className="w-full bg-transparent border-0 border-b border-[var(--color-primary)]/40 focus:border-[var(--color-primary)] focus:ring-0 px-0 py-3 text-[var(--color-on-surface)] font-[family-name:var(--font-body-lg)] text-lg transition-colors placeholder:text-[var(--color-on-surface-variant)]/30 focus:outline-none"
            />
          </div>

          <div className="relative group mb-4">
            <label
              htmlFor="password"
              className={`block ${hFont(locale)} text-xs text-[var(--color-on-surface-variant)] mb-2 group-focus-within:text-[var(--color-primary)] uppercase tracking-wider transition-colors`}
            >
              {t.passLabel}
            </label>
            <input
              type="password"
              id="password"
              name="password"
              placeholder="••••••••••••"
              required
              dir="ltr"
              className="w-full bg-transparent border-0 border-b border-[var(--color-primary)]/40 focus:border-[var(--color-primary)] focus:ring-0 px-0 py-3 text-[var(--color-on-surface)] font-[family-name:var(--font-body-lg)] text-lg transition-colors tracking-widest focus:outline-none"
            />
          </div>

          <button
            type="submit"
            className={`w-full py-5 border-2 border-[var(--color-primary)] bg-transparent text-[var(--color-primary)] ${hFont(locale)} text-xs uppercase tracking-[0.2em] hover:bg-[var(--color-primary)] hover:text-[#3d2e00] transition-all duration-300 mt-2`}
          >
            {t.submit}
          </button>
        </form>

        <footer className="mt-8 text-center">
          <Link
            href="#"
            className={`${hFont(locale)} text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)] transition-colors opacity-70 hover:opacity-100 text-sm`}
          >
            {t.requestAccess}
          </Link>
        </footer>
      </main>
    </div>
  );
}
