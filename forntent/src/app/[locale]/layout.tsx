export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const p = await params;
  const locale = p.locale as "en" | "ar";
  const isRTL = locale === "ar";

  return (
    <div
      dir={isRTL ? "rtl" : "ltr"}
      lang={locale}
      className={isRTL ? "w-full min-h-screen flex flex-col font-(family-name:--font-almarai)" : "w-full min-h-screen flex flex-col"}
    >
      {children}
    </div>
  );
}
