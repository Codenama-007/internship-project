import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // NEXT_LIVE_URL has no NEXT_PUBLIC_ prefix, so expose it to the browser bundle.
  env: { NEXT_LIVE_URL: process.env.NEXT_LIVE_URL },
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
