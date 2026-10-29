# XRazor

XRazor is a tool for cleaning web artifacts into AI-readable context.

It currently supports:

- HTML cleaning
- HAR cleaning
- AI-friendly context export

## Overview

XRazor turns noisy web files into input that is easier for AI to understand.

Common use cases:

- simplify saved HTML or browser DOM snapshots
- reduce HAR files to the requests and responses that matter
- generate a quick page or API summary for AI workflows

## Supported Input

- `.html`
- `.htm`
- `.har`

## Install

```powershell
python -m pip install -e .
```

The browser-friendly TypeScript core is available under `packages/core`:

```powershell
npm install
```

```ts
import { cleanHtmlText, cleanHar } from "@xrazor/core";

const htmlResult = cleanHtmlText(html);
const harResult = cleanHar(JSON.parse(harText));
```

The Python and TypeScript implementations are maintained as separate runtimes. They share the same cleaning rules and are intended for different integration scenarios.

### Browser build

Build the browser distributions with:

```powershell
npm run build:browser
```

This produces:

```text
packages/core/dist/index.js         # ES module
packages/core/dist/index.global.js  # IIFE browser bundle
packages/core/dist/index.d.ts       # Type declarations
```

The IIFE bundle exposes the API as `window.XRazor`:

```html
<script src="./packages/core/dist/index.global.js"></script>
<script>
  const result = XRazor.cleanHar({ log: { entries: [] } });
</script>
```

`cleanHar` and `cleanHarText` are pure JavaScript and work in browsers, Web Workers, and Node.js. `cleanHtmlText` requires a browser DOM environment providing `DOMParser`, `NodeFilter`, and `XMLSerializer`. For an existing page DOM, use `cleanHtmlDocument(document)`.

### Validation and release

Run the JavaScript checks locally with:

```powershell
npm ci
npm run typecheck:js
npm run test:js
npm run build:browser
npm run test:browser-bundle
npx playwright install chromium
npm run test:real-browser
```

The Python implementation remains independently testable:

```powershell
python -m pytest -q
```

Before publishing `@xrazor/core`, inspect the package contents with:

```powershell
Push-Location packages/core
npm pack --dry-run
Pop-Location
```

The current package version is `@xrazor/core@0.1.1`. Downstream applications should use this released version once published, or pin a specific commit while release packaging is being prepared. They should not follow `main` directly.

## Basic Usage

Run commands with either `python -m xrazor` or `xrazor`.

### Clean HTML

```powershell
python -m xrazor clean tt_page.html --out cleaned.html
```

### Clean HAR

```powershell
python -m xrazor clean item_list.har --out cleaned.har.json
```

### Export Structured Output

```powershell
python -m xrazor export tt_page.html --format json
python -m xrazor export tt_page.html --format markdown

python -m xrazor export item_list.har --format json
python -m xrazor export item_list.har --format markdown
```

### Export AI Context

```powershell
python -m xrazor context tt_page.html
python -m xrazor context item_list.har
```

## Output Style

XRazor is designed for AI readability, not browser replay.

- non-essential content may be removed
- useful structure is kept where possible
- replaced values use stable `[xrazor]...` placeholders

Example placeholders:

- `[xrazor]filtered-base64-content`
- `[xrazor]trimmed-long-text`
- `[xrazor]removed-binary-content`

## Current Focus

- cleaner HTML structure
- smaller and more useful HAR output
- faster AI understanding of page structure and API activity
