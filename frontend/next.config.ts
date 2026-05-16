import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Monorepo root (repo root on Vercel). outputFileTracingRoot and turbopack.root must match.
const appDir = path.dirname(fileURLToPath(import.meta.url));
const monorepoRoot = path.resolve(appDir, "..");

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: monorepoRoot,
  turbopack: {
    root: monorepoRoot,
  },
};

export default nextConfig;
