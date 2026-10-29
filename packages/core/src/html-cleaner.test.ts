// @vitest-environment jsdom

import { describe, expect, it } from "vitest";
import { cleanHtmlText } from "./html-cleaner";

describe("cleanHtmlText", () => {
  it("removes noisy nodes and preserves useful content", () => {
    const result = cleanHtmlText(`
      <html><body>
        <!-- remove me -->
        <script>alert(1)</script>
        <style>.hidden { display: none }</style>
        <button onclick="submit()" data-testid="save"> Save </button>
        <div class="content css-abc123 abcdef123456 hero-banner"> Hello   world </div>
      </body></html>
    `);

    expect(result.content).not.toContain("<script");
    expect(result.content).not.toContain("<style");
    expect(result.content).not.toContain("remove me");
    expect(result.content).not.toContain("onclick");
    expect(result.content).toContain('data-testid="save"');
    expect(result.content).toContain('class="hero-banner"');
    expect(result.content).toContain("Hello world");
  });

  it("rewrites base64 images and supports image removal", () => {
    const stripped = cleanHtmlText('<html><body><img src="data:image/png;base64,AAAA" alt="sample"></body></html>');
    expect(stripped.content).toContain("[xrazor]filtered-base64-content");

    const removed = cleanHtmlText('<html><body><img src="https://example.com/a.png"><div>ok</div></body></html>', {
      imageMode: "remove",
    });
    expect(removed.content).not.toContain("<img");
    expect(removed.content).toContain("ok");
  });

  it("removes empty non-interactive nodes", () => {
    const result = cleanHtmlText(`
      <html><body>
        <div id="keep-me"></div>
        <div class="empty"><span></span></div>
        <button></button>
        <input name="query">
      </body></html>
    `);

    expect(result.content).toContain('id="keep-me"');
    expect(result.content).not.toContain('class="empty"');
    expect(result.content).toContain("<button");
    expect(result.content).toContain('name="query"');
  });

});
