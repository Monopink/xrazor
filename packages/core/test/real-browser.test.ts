import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { chromium } from "playwright";
import { afterAll, describe, expect, it } from "vitest";

const browserPromise = chromium.launch({ headless: true });

afterAll(async () => {
  const browser = await browserPromise;
  await browser.close();
});

describe("real browser bundle", () => {
  it("loads and exposes the API in Chromium", async () => {
    const browser = await browserPromise;
    const page = await browser.newPage();
    const bundlePath = resolve(process.cwd(), "packages/core/dist/index.global.js");
    await page.goto("about:blank");
    await page.addScriptTag({ content: readFileSync(bundlePath, "utf8") });

    const result = await page.evaluate(() => {
      const api = (window as unknown as {
        XRazor: {
          cleanHar: (har: unknown) => { content: { _xrazor_note: string } };
          cleanHtmlText: (html: string) => { content: string };
        };
      }).XRazor;
      return {
        har: api.cleanHar({ log: { entries: [] } }).content._xrazor_note,
        html: api.cleanHtmlText("<html><body><script>x()</script><p>Hello</p></body></html>").content,
      };
    });

    expect(result.har).toContain("XRazor");
    expect(result.html).toContain("Hello");
    expect(result.html).not.toContain("<script");
    await page.close();
  });
});
