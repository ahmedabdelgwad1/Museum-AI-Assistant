"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Globe } from "lucide-react";

export function GlobalNavigation({ locale }: { locale: "en" | "ar" }) {
  const pathname = usePathname();
  const isWelcomePage = pathname === `/${locale}/welcome` || pathname === `/`;

  // Don't show on welcome page
  if (isWelcomePage) return null;

  const isRTL = locale === "ar";
  
  return (
    <div className={`fixed top-4 ${isRTL ? "left-4" : "right-4"} z-50`}>
      <Link 
        href={`/${locale}/welcome`}
        className="flex items-center gap-2 px-4 py-2 bg-bg-card/80 backdrop-blur-md border border-border rounded-full text-text-secondary hover:text-gold hover:border-gold transition-all shadow-lg group"
      >
        <Home className="w-4 h-4" />
        <span className={`text-xs uppercase tracking-widest ${isRTL ? "font-(family-name:--font-almarai)" : "font-(family-name:--font-inter)"}`}>
          {isRTL ? "الرئيسية" : "Home"}
        </span>
      </Link>
    </div>
  );
}
