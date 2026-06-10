import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Explicitly set turbopack root to this project's directory.
  // Prevents Next.js from getting confused by multiple package-lock.json files
  // found in parent directories (e.g. /Users/apple/package-lock.json).
  turbopack: {
    root: path.resolve(__dirname),
  },

  // ✅ تحسين الأداء - تقليل استهلاك CPU
  typescript: {
    // تعطيل type checking أثناء الـ build (اعمله منفصل بـ tsc)
    ignoreBuildErrors: false,
  },
  
  // تقليل الـ source maps في الـ development لتوفير memory
  productionBrowserSourceMaps: false,
};

export default nextConfig;
