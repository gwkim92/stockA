// @vitest-environment node
import { describe, expect, it } from "vitest";
import { buildBlockReason } from "../scripts/build.mjs";

describe("production build isolation", () => {
  it.each([
    "/opt/stockanalysis/app/apps/web",
    "/opt/stockanalysis/runtime/research-automation-20260911/build/apps/web",
    "/opt/stockanalysis/runtime/../app/apps/web",
  ])("blocks the live checkout and separate runtime builds: %s", (projectRoot) => {
    expect(buildBlockReason({ projectRoot })).not.toBeNull();
  });
  it("blocks another checkout directory on an EC2 host", () => {
    expect(buildBlockReason({ projectRoot: "/home/ec2-user/app/apps/web", systemVendor: "Amazon EC2\n" })).not.toBeNull();
  });
  it.each(["/Users/woody/Documents/ChatGPT/stockA/apps/web", "/home/runner/work/stockA/stockA/apps/web", "/build/apps/web"])("allows separate development and CI builds: %s", (projectRoot) => {
    expect(buildBlockReason({ projectRoot, systemVendor: "Microsoft Corporation" })).toBeNull();
  });
});
