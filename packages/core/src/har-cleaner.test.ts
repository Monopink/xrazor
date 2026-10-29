import { describe, expect, it } from "vitest";
import { cleanHar } from "./har-cleaner";

describe("cleanHar", () => {
  it("drops scripts and trims JSON response bodies", () => {
    const result = cleanHar({ log: { entries: [
      { _resourceType: "script", request: { url: "https://example.com/app.js" }, response: { content: { mimeType: "application/javascript" } } },
      { _resourceType: "xhr", request: { method: "GET", url: "https://example.com/api" }, response: { status: 200, content: { mimeType: "application/json", text: '{"ok":true}' } } },
    ] } });
    expect(result.content.log?.entries).toHaveLength(1);
    expect(result.content.log?.entries?.[0]?.response.content.json).toEqual({ ok: true });
  });
});
