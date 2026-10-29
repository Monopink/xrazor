import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["packages/**/*.test.ts"],
    exclude: [
      "packages/core/test/browser-bundle.test.ts",
      "packages/core/test/real-browser.test.ts",
    ],
  },
});
