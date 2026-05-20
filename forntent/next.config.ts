import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Explicitly set turbopack root to this project's directory.
  // Prevents Next.js from getting confused by multiple package-lock.json files
  // found in parent directories (e.g. /Users/apple/package-lock.json).
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
