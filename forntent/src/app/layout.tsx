import type { Metadata } from "next";
import { Inter, Almarai } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const almarai = Almarai({ subsets: ["arabic"], weight: ["300", "400", "700", "800"], variable: "--font-almarai" });

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
    <html suppressHydrationWarning className={`${inter.variable} ${almarai.variable}`}>
      <body>{children}</body>
    </html>
  );
}
