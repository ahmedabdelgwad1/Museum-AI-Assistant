"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Library, PlusCircle, Users, Settings, LogOut,
} from "lucide-react";
import { getDictionary } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";

export function AdminSidebar({ locale: _localeProp }: { locale: string }) {
  const pathname = usePathname();
  const { locale, setLocale } = useAdminLocale();
  const t = getDictionary(locale as "en" | "ar").admin;
  const isRTL = locale === "ar";

  const NAV_ITEMS = [
    { href: `/admin`,               label: t.nav.overview,      icon: LayoutDashboard, exact: true  },
    { href: `/admin/artifacts`,     label: t.nav.collection,    icon: Library,         exact: false },
    { href: `/admin/artifacts/new`, label: t.nav.acquisitions,  icon: PlusCircle,      exact: true  },
    { href: `/admin/settings`,      label: t.nav.settings,      icon: Settings,        exact: false },
  ];

  // Custom active check:
  // - 'exact' items: must match pathname exactly
  // - Collection (/artifacts): active when on /artifacts OR sub-pages EXCEPT /artifacts/new
  // - Settings: startsWith match
  const isActive = (href: string, exact: boolean) => {
    if (exact) return pathname === href;
    if (href === `/admin/artifacts`) {
      return pathname.startsWith(href) && pathname !== `/admin/artifacts/new`;
    }
    return pathname.startsWith(href);
  };

  return (
    <nav
      dir={isRTL ? "rtl" : "ltr"}
      className={`fixed top-0 h-full flex flex-col pt-8 pb-6 z-50 bg-[#0a0a0f] border-[var(--color-primary)]/20 shadow-[4px_0_24px_rgba(0,0,0,0.6)] w-64 hidden md:flex ${isRTL ? "right-0 border-l" : "left-0 border-r"}`}
    >
      {/* Brand */}
      <div className="px-6 mb-10 flex flex-col items-center text-center">
        <div className="w-16 h-16 rounded-full border border-[var(--color-primary)]/40 overflow-hidden mb-4 bg-[#1a1825] shrink-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            alt="Museum Seal"
            className="w-full h-full object-cover grayscale opacity-80"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuD90VcCkV6yFG2FPXZEXVtAMyGsxKXYKHLBK_-ajGhrY5LMmpqbb5gD_27MO-jOinkZ21iEzpfxa_20dNHFxnAbcod7U9dUKnP91a-ndmjVeA6PQfHPHcNnDQ7VNZfgLGdaMOixF8TW6cRBwr0xSNFF07Y1JpzTnQ2q_MQ9q9zpUbuudCAo98yk9-0sSMUqWGvFQs3J_ziYgOw6R0kTcgUHG7yE_XJ3cO8rQpzWkbAL0WK-yO6vELCMcZGvUhVJklT5b2N5Cb_pLUY"
          />
        </div>
        <h1 className={`text-sm font-bold text-[var(--color-primary)] tracking-widest uppercase leading-tight ${isRTL ? "font-[family-name:var(--font-arabic)]" : "font-[family-name:var(--font-headline-md)]"}`}>
          {t.brand}
        </h1>
        <p className="text-[10px] text-gray-500 mt-1 font-[family-name:var(--font-label-sm)] uppercase tracking-widest">
          {t.brandSub}
        </p>
      </div>

      {/* Quick CTA */}
      <div className="px-6 mb-8">
        <Link
          href="/admin/artifacts/new"
          className="w-full border border-[var(--color-primary)] text-[var(--color-primary)] py-2 font-[family-name:var(--font-label-sm)] uppercase tracking-widest text-xs transition-all duration-300 hover:bg-[var(--color-primary)] hover:text-[#0a0a0f] flex justify-center items-center gap-2"
        >
          <PlusCircle size={15} /> {t.addArtifact}
        </Link>
      </div>

      {/* Nav */}
      <ul className="flex-1 flex flex-col gap-1 px-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon, exact }) => {
          const active = isActive(href, exact);
          return (
            <li key={label}>
              <Link
                href={href}
                className={`flex items-center gap-4 px-4 py-3 font-[family-name:var(--font-label-sm)] uppercase tracking-widest text-xs rounded-sm transition-all duration-300 ${
                  active
                    ? `text-[var(--color-primary)] bg-[var(--color-primary)]/10 ${isRTL ? "border-l-2" : "border-r-2"} border-[var(--color-primary)]`
                    : "text-gray-500 hover:text-[var(--color-primary)]/80 hover:bg-[#1a1825]"
                }`}
              >
                <Icon size={18} />
                {label}
              </Link>
            </li>
          );
        })}

        {/* Scholars — coming soon */}
        <li>
          <span className="flex items-center gap-4 px-4 py-3 font-[family-name:var(--font-label-sm)] uppercase tracking-widest text-xs text-gray-600 cursor-not-allowed">
            <Users size={18} />
            {isRTL ? "الباحثون" : "Scholars"}
            <span className="ml-auto text-[9px] border border-gray-700 text-gray-700 px-1 py-0.5 rounded tracking-normal normal-case">
              {t.nav.soon}
            </span>
          </span>
        </li>
      </ul>

      {/* Footer */}
      <div className="px-2 pt-4 border-t border-[var(--color-primary)]/10">
        {/* Language Switch */}
        <div className="flex gap-2 px-4 mb-3">
          <button
            onClick={() => setLocale("en")}
            className={`flex-1 text-center py-1 text-[10px] font-[family-name:var(--font-label-sm)] uppercase tracking-widest border transition-colors ${
              locale === "en"
                ? "border-[var(--color-primary)] text-[var(--color-primary)] bg-[var(--color-primary)]/10"
                : "border-gray-700 text-gray-500 hover:border-[var(--color-primary)]/50 hover:text-[var(--color-primary)]/70"
            }`}
          >EN</button>
          <button
            onClick={() => setLocale("ar")}
            className={`flex-1 text-center py-1 text-sm font-[family-name:var(--font-arabic)] border transition-colors ${
              locale === "ar"
                ? "border-[var(--color-primary)] text-[var(--color-primary)] bg-[var(--color-primary)]/10"
                : "border-gray-700 text-gray-500 hover:border-[var(--color-primary)]/50 hover:text-[var(--color-primary)]/70"
            }`}
          >ع</button>
        </div>

        <Link
          href={`/${locale}/welcome`}
          className="flex items-center gap-4 px-4 py-3 font-[family-name:var(--font-label-sm)] uppercase tracking-widest text-xs text-gray-500 hover:text-[var(--color-primary)]/80 hover:bg-[#1a1825] rounded-sm transition-all duration-300"
        >
          <LogOut size={18} />
          {t.nav.exit}
        </Link>
      </div>
    </nav>
  );
}
