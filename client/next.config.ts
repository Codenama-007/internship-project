import type { NextConfig } from "next";

// Single place the browser talks to: /api/* is rewritten to FastAPI, so no CORS.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
