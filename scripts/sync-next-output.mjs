import { cpSync, existsSync, rmSync } from "node:fs";
import path from "node:path";

const src = path.join("frontend", ".next");
const dest = ".next";

if (!existsSync(src)) {
  console.error("Expected build output at frontend/.next but it was not found.");
  process.exit(1);
}

rmSync(dest, { recursive: true, force: true });
cpSync(src, dest, { recursive: true });
console.log("Synced frontend/.next -> .next for Vercel");
