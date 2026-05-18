import type { Metadata } from "next";
import { Cinzel, Cormorant_Garamond, Noto_Naskh_Arabic } from "next/font/google";
import "./globals.css";

const cinzel = Cinzel({ subsets: ["latin"], variable: "--font-cinzel" });
const cormorant = Cormorant_Garamond({ subsets: ["latin"], weight: ["400", "700"], variable: "--font-cormorant" });
const notoNaskh = Noto_Naskh_Arabic({ subsets: ["arabic"], weight: ["400", "500", "700"], variable: "--font-noto-naskh" });

export const metadata: Metadata = {
  title: "Bibliotheca Alexandrina - Antiquities Museum",
  description: "Museum chatbot system UI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html suppressHydrationWarning className={`${cinzel.variable} ${cormorant.variable} ${notoNaskh.variable}`}>
      <body>{children}</body>
    </html>
  );
}
