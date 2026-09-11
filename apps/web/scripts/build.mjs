import { readFileSync, realpathSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

export function buildBlockReason({ projectRoot, systemVendor = "" }) {
  const root = resolve(projectRoot);
  if (root === "/opt/stockanalysis" || root.startsWith("/opt/stockanalysis/")) {
    return "stockA production or runtime directory";
  }
  if (/^Amazon EC2$/i.test(systemVendor.trim())) {
    return "Amazon EC2 host";
  }
  return null;
}

function main() {
  const projectRoot = realpathSync(fileURLToPath(new URL("../", import.meta.url)));
  let systemVendor = "";
  if (process.platform === "linux") {
    try {
      systemVendor = readFileSync("/sys/class/dmi/id/sys_vendor", "utf8");
    } catch {
      // Containers may not expose DMI. The production path guard still applies.
    }
  }
  const reason = buildBlockReason({ projectRoot, systemVendor });
  if (reason) {
    console.error(`Build blocked on ${reason}. Download the verified Web Runtime Artifact from CI. No compiler was started.`);
    process.exitCode = 1;
    return;
  }
  const require = createRequire(import.meta.url);
  const result = spawnSync(process.execPath, [require.resolve("next/dist/bin/next"), "build", ...process.argv.slice(2)], {
    cwd: projectRoot,
    stdio: "inherit",
    env: process.env,
  });
  if (result.error) console.error(result.error.message);
  process.exitCode = result.status ?? 1;
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) main();
