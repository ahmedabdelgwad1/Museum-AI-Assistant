/**
 * Central i18n helper — returns full typed translations for a given locale.
 * All hard-coded UI strings across every screen must come from here.
 */
import en from "../messages/en.json";
import ar from "../messages/ar.json";

const dictionaries = { en, ar } as const;

export type Locale = "en" | "ar";

export const getDictionary = (locale: Locale | string) =>
  dictionaries[(locale as Locale) in dictionaries ? (locale as Locale) : "en"];

/** CSS class helpers */
export const rtl = (locale: string) => locale === "ar";
export const dir = (locale: string) => (locale === "ar" ? "rtl" : "ltr");
export const hFont = (locale: string) =>
  locale === "ar"
    ? "font-[family-name:var(--font-arabic)]"
    : "font-[family-name:var(--font-headline-md)]";
export const bodyFont = (locale: string) =>
  locale === "ar"
    ? "font-[family-name:var(--font-arabic)]"
    : "font-[family-name:var(--font-body-md)]";
