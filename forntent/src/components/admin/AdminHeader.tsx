import { Bell, UserCircle, Search } from "lucide-react";
import Link from "next/link";
import { getDictionary } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";

export function AdminHeader({ locale: _localeProp }: { locale: string }) {
  const { locale } = useAdminLocale();
  const t = getDictionary(locale as "en" | "ar").admin;
  const isRTL = locale === "ar";

  return (
    <header
      dir={isRTL ? "rtl" : "ltr"}
      className={`fixed top-0 right-0 z-40 bg-[#0a0a0f]/80 backdrop-blur-md h-16 border-b border-[var(--color-primary)]/20 flex items-center justify-between px-6 md:px-8 gap-4 ${isRTL ? "left-0 md:left-0 md:right-64" : "left-0 md:left-64"}`}
    >
      {/* Mobile brand */}
      <span className={`md:hidden text-[var(--color-primary)] text-sm uppercase tracking-widest ${isRTL ? "font-[family-name:var(--font-arabic)]" : "font-[family-name:var(--font-headline-md)]"}`}>
        {t.brand}
      </span>

      {/* Search bar */}
      <div className="relative group hidden sm:block flex-1 max-w-xs">
        <Search
          size={16}
          className={`absolute top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-[var(--color-primary)] transition-colors pointer-events-none ${isRTL ? "right-0" : "left-0"}`}
        />
        <input
          type="text"
          placeholder={t.header.search}
          dir={isRTL ? "rtl" : "ltr"}
          className={`w-full bg-transparent border-0 border-b border-[var(--color-primary)]/30 py-1 text-sm text-[var(--color-on-surface)] placeholder-gray-600 focus:ring-0 focus:border-[var(--color-primary)] focus:outline-none transition-colors ${isRTL ? "pr-6 pl-4 text-right font-[family-name:var(--font-arabic)]" : "pl-6 pr-4"}`}
        />
      </div>

      {/* Right actions */}
      <div className={`flex items-center gap-4 ${isRTL ? "mr-auto" : "ml-auto"}`}>
        <button aria-label="Notifications" className="text-gray-500 hover:text-[var(--color-primary)] transition-colors">
          <Bell size={20} />
        </button>

        <Link
          href="/admin/settings"
          aria-label="Profile settings"
          className="text-gray-500 hover:text-[var(--color-primary)] transition-colors"
        >
          <UserCircle size={22} />
        </Link>


      </div>
    </header>
  );
}
