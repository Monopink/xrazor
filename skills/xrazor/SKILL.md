---
name: xrazor
description: Clean HTML files, browser DOM snapshots, and HAR files into AI-readable context. Use when a task involves noisy web page source, exported browser DOM, or network captures and Codex should first simplify them before analyzing structure, extracting UI elements, or reviewing API activity.
---

# XRazor

Use XRazor before reasoning deeply about HTML or HAR artifacts.

XRazor is a preprocessing skill for web artifacts. It reduces noise, preserves useful structure, and produces compact summaries that are easier for Codex to work with.

## Quick Start

From the XRazor project root, use the CLI in this order:

1. Run `context` when you need a fast summary.
2. Run `clean` when you need a transformed artifact to inspect or pass downstream.
3. Run `export` when you need structured JSON or markdown output.

Examples:

```powershell
python -m xrazor context page.html
python -m xrazor context page.har
python -m xrazor clean page.html --out cleaned.html
python -m xrazor clean page.har --out cleaned.har.json
python -m xrazor export page.html --format json
python -m xrazor export page.har --format markdown
```

Read `references/cli.md` when you need the available commands and mode switches.

## Workflow

### HTML

Use XRazor on HTML when:

- the page source is full of scripts, styles, framework classes, and tracking attributes
- you need buttons, inputs, links, titles, or visible stats
- you need a smaller artifact before asking Codex to analyze page structure

Default behavior is conservative:

- remove non-essential nodes
- keep useful attributes
- preserve meaningful structure
- mark replaced values with `[xrazor]...`

If the cleaned HTML is still too noisy:

- use `--class-mode none` to drop classes
- use `--image-mode remove` to remove images entirely

### HAR

Use XRazor on HAR when:

- the capture is dominated by static assets or telemetry
- you want the main API calls and response types
- you need a compact network summary before deeper analysis

XRazor keeps the request and response information most useful for AI reading and emits a concise API-focused context summary.

## Working Rules

- Treat XRazor output as AI-oriented transformed data, not replay-accurate browser data.
- Prefer `context` first when the user only needs understanding.
- Prefer `clean` when another tool or prompt will consume the transformed artifact.
- Prefer `export --format json` when downstream processing needs structure.
- Do not assume every HAR contains full response bodies.
- Expect `[xrazor]...` placeholders where large, binary, or filtered values were simplified.
