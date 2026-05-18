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
  const [locale, setLocaleState] = useState<Locale>("en");

  // Read from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("admin-locale") as Locale | null;
    if (saved === "ar" || saved === "en") {
      setLocaleState(saved);
    }
  }, []);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem("admin-locale", newLocale);
  };

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
