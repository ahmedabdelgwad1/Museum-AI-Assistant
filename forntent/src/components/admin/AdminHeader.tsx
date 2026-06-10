import { Bell, UserCircle, Search } from "lucide-react";
import Link from "next/link";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { getDictionary } from "@/lib/dictionaries";
import { useAdminLocale } from "@/context/AdminLocaleContext";

export function AdminHeader({ locale: _localeProp }: { locale: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const { locale } = useAdminLocale();
  const t = getDictionary(locale as "en" | "ar").admin;
  const isRTL = locale === "ar";

  return (
    <header
      dir={isRTL ? "rtl" : "ltr"}
      className={`fixed top-0 right-0 z-40 bg-bg-primary/80 backdrop-blur-md h-16 border-b border-primary/20 flex items-center justify-between px-6 md:px-8 gap-4 ${isRTL ? "left-0 md:left-0 md:right-64" : "left-0 md:left-64"}`}
    >
      {/* Mobile brand */}
      <span className={`md:hidden text-primary text-sm uppercase tracking-widest ${isRTL ? "font-(family-name:--font-almarai)" : "font-(family-name:--font-headline-md)"}`}>
        {t.brand}
      </span>

      {/* Search bar */}
      <div className="relative group hidden sm:block flex-1 max-w-xs">
        <Search
          size={16}
          className={`absolute top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-primary transition-colors pointer-events-none ${isRTL ? "right-0" : "left-0"}`}
        />
        <input
          type="text"
          placeholder={t.header.search}
          dir={isRTL ? "rtl" : "ltr"}
          defaultValue={searchParams.get("q") || ""}
          onChange={(e) => {
            const params = new URLSearchParams(searchParams.toString());
            if (e.target.value) {
              params.set("q", e.target.value);
            } else {
              params.delete("q");
            }
            router.replace(`${pathname}?${params.toString()}`);
          }}
          className={`w-full bg-transparent border-0 border-b border-primary/30 py-1 text-sm text-on-surface placeholder-gray-600 focus:ring-0 focus:border-primary focus:outline-none transition-colors ${isRTL ? "pr-6 pl-4 text-right font-(family-name:--font-almarai)" : "pl-6 pr-4"}`}
        />
      </div>

      {/* Right actions */}
      <div className={`flex items-center gap-4 ${isRTL ? "mr-auto" : "ml-auto"}`}>
        <button aria-label="Notifications" className="text-gray-500 hover:text-primary transition-colors">
          <Bell size={20} />
        </button>

        <Link
          href="/admin/settings"
          aria-label="Profile settings"
          className="text-gray-500 hover:text-primary transition-colors"
        >
          <UserCircle size={22} />
        </Link>


      </div>
    </header>
  );
}
