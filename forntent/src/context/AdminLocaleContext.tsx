"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";

type Locale = "en" | "ar";

interface AdminLocaleContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

const AdminLocaleContext = createContext<AdminLocaleContextType>({
  locale: "en",
  setLocale: () => {},
});

export function AdminLocaleProvider({ children }: { children: ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    const saved = window.localStorage.getItem("admin-locale") as Locale | null;
    if (saved === "ar" || saved === "en") {
      setLocaleState(saved);
    }
    setMounted(true);
  }, []);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    window.localStorage.setItem("admin-locale", newLocale);
  };

  if (!mounted) {
    return null; // Prevents hydration mismatch
  }

  return (
    <AdminLocaleContext.Provider value={{ locale, setLocale }}>
      <div dir={locale === "ar" ? "rtl" : "ltr"} lang={locale}>
        {children}
      </div>
    </AdminLocaleContext.Provider>
  );
}

export function useAdminLocale() {
  return useContext(AdminLocaleContext);
}
