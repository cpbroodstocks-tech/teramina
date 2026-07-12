import { readdir, stat } from "node:fs/promises";
import { join, relative } from "node:path";

const DIST_DIR = new URL("../dist/", import.meta.url);
const MAX_CHUNK_BYTES = 500 * 1024;
const MAX_TOTAL_JS_BYTES = 3 * 1024 * 1024;
const files = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await walk(path);
    else files.push({ path, size: (await stat(path)).size });
  }
}

await walk(DIST_DIR.pathname);

const javascript = files.filter(({ path }) => path.endsWith(".js"));
const largest = javascript.reduce((current, file) => file.size > current.size ? file : current, { size: 0, path: "" });
const total = javascript.reduce((sum, file) => sum + file.size, 0);
const failures = [];

if (largest.size > MAX_CHUNK_BYTES) failures.push(`Largest JS chunk exceeds 500 KiB: ${relative(DIST_DIR.pathname, largest.path)} (${largest.size} bytes)`);
if (total > MAX_TOTAL_JS_BYTES) failures.push(`Total JS exceeds 3 MiB: ${total} bytes`);

console.log(`Bundle budget: ${javascript.length} JS files, ${total} bytes total, ${largest.size} bytes largest.`);
if (failures.length) {
  failures.forEach((failure) => console.error(failure));
  process.exit(1);
}
