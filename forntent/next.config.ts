import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    // Other experimental features if any
  },
  // @ts-ignore - turbopack might not be fully typed in this version
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
