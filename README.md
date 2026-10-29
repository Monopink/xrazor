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
