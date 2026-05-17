import type { NextConfig } from "next";

// Standalone is for Docker only; Vercel uses its own Next.js output pipeline.
const nextConfig: NextConfig = {
  ...(process.env.DOCKER_BUILD === "1" ? { output: "standalone" as const } : {}),
};

export default nextConfig;
