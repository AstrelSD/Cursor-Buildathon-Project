import type { NextConfig } from "next";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const appDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(appDir, "..");
// When Vercel builds from the repo root, tracing root must match /vercel/path0.
const tracingRoot = existsSync(path.join(repoRoot, "package.json"))
  ? repoRoot
  : appDir;

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: tracingRoot,
};

export default nextConfig;
