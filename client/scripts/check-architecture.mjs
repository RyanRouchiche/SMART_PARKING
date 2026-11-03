import { readdirSync, readFileSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = resolve(dirname(fileURLToPath(import.meta.url)), "../src");
const FEATURES = ["auth", "parking", "cameras", "detection"];
const IMPORT = /(?:import|export)\s[^'"]*?from\s*["']([^"']+)["']|import\s*\(?\s*["']([^"']+)["']/g;

function files(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      return files(path);
    }
    return /\.(jsx?|mjs)$/.test(entry.name) ? [path] : [];
  });
}

function area(path) {
  const parts = relative(SRC, path).split(sep);
  return parts[0] === "features" ? { kind: "feature", name: parts[1], parts } : { kind: parts[0], parts };
}

function check(file) {
  const source = readFileSync(file, "utf8");
  const from = area(file);
  const where = relative(SRC, file).split(sep).join("/");
  const problems = [];

  for (const match of source.matchAll(IMPORT)) {
    const spec = match[1] ?? match[2];
    if (!spec.startsWith(".")) {
      continue;
    }
    const to = area(resolve(dirname(file), spec));
    if (from.kind === "shared" && to.kind !== "shared") {
      problems.push(`${where}: shared must not import ${spec}`);
    } else if (from.kind === "feature" && to.kind === "app") {
      problems.push(`${where}: features must not import the app layer (${spec})`);
    } else if (from.kind === "feature" && to.kind === "feature" && to.name !== from.name) {
      if (FEATURES.indexOf(to.name) > FEATURES.indexOf(from.name)) {
        problems.push(`${where}: ${from.name} may only use lower features (${spec})`);
      } else if (to.parts.length !== 3 || to.parts[2] !== "index.js") {
        problems.push(`${where}: import ${to.name} through features/${to.name}/index.js (${spec})`);
      }
    }
  }

  if (/\bfetch\(/.test(source) && where !== "shared/http.js") {
    problems.push(`${where}: only shared/http.js may call fetch`);
  }
  if (/\bapi\(\s*[`"']/.test(source) && !/^features\/[^/]+\/api\.js$/.test(where)) {
    problems.push(`${where}: API URLs belong in the feature's api.js`);
  }
  return problems;
}

const problems = files(SRC).flatMap(check);
if (problems.length) {
  console.error(["Architecture rules broken:", ...problems].join("\n  "));
  process.exit(1);
}
console.log(`Architecture OK (${files(SRC).length} files)`);
