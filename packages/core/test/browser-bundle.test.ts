import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

describe("browser bundle", () => {
  it("exposes the public API through the XRazor global", () => {
    const bundlePath = resolve(process.cwd(), "packages/core/dist/index.global.js");
    const bundle = readFileSync(bundlePath, "utf8");
    const dom = new JSDOM("<!doctype html><html><body></body></html>", {
      runScripts: "dangerously",
    });

    const script = dom.window.document.createElement("script");
    script.textContent = bundle;
    dom.window.document.body.appendChild(script);
    const api = (dom.window as unknown as { XRazor?: { cleanHar: Function } }).XRazor;

    expect(api).toBeDefined();
    if (!api) throw new Error("Browser bundle did not expose window.XRazor");
    const result = api.cleanHar({ log: { entries: [] } });

    expect(result.content._xrazor_note).toContain("XRazor");
  });
});
