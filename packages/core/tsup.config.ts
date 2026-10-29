import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm", "iife"],
  globalName: "XRazor",
  outDir: "dist",
  dts: true,
  minify: true,
  sourcemap: true,
  clean: true,
  target: "es2020",
  outExtension: ({ format }) => ({
    js: format === "iife" ? ".global.js" : ".js",
  }),
});
