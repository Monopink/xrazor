# XRazor Agent Notes

## Goal

XRazor converts web artifacts into AI-readable context. It is not an HTML minifier, HAR compressor, or browser replay tool.

The first implementation phase focuses on:

- conservative HTML cleaning
- conservative HAR cleaning
- explicit AI-facing notes about removed or simplified content
- stable CLI and config foundations

## Product Boundaries

- Output is optimized for LLM comprehension, not browser execution.
- HTML input may be either server HTML or browser-final DOM. V1 is biased toward browser-final DOM.
- HAR remains the primary network input format in V1.
- Large JSON must not be hard-truncated as text.
- Removed content should be deleted when its position is not meaningful.
- Replaced content must keep the original field or attribute name and replace only the value.

## Marking Rules

- Every transformed artifact starts with a short XRazor note.
- Replaced values use a standard placeholder prefix: `[xrazor]`.
- Prefer short fixed phrases over free-form descriptions.

Examples:

- `src="[xrazor]filtered-base64-content"`
- `text="[xrazor]trimmed-long-text"`
- `response.content.text="[xrazor]removed-binary-content"`

## Conservative Defaults

### HTML

- remove whole nodes:
  - `script`
  - `style`
  - `noscript`
  - `svg`
  - `canvas`
  - `iframe`
  - `template`
  - `link`
  - `meta`
  - `source`
  - `picture`
- remove comments
- collapse repeated whitespace in text nodes
- keep useful attributes by default:
  - `id`
  - `name`
  - `type`
  - `href`
  - `src`
  - `value`
  - `placeholder`
  - `title`
  - `role`
  - `alt`
  - `action`
  - `method`
  - `for`
- keep selected ARIA attributes:
  - `aria-label`
  - `aria-labelledby`
  - `aria-describedby`
- keep selected data attributes:
  - `data-testid`
  - `data-test`
  - `data-e2e`
- keep readable classes, drop obvious hash-like classes
- remove empty nodes only when they have no text, no children, no meaningful attributes, and are not interactive

### HAR

- keep resource types:
  - `document`
  - `xhr`
  - `fetch`
- drop by default:
  - `script`
  - `stylesheet`
  - `image`
  - `font`
  - `media`
  - `websocket`
- remove non-essential headers such as:
  - `sec-ch-*`
  - `sec-fetch-*`
  - `accept-language`
  - `accept-encoding`
  - `priority`
  - `cookie`
  - `etag`
  - `expires`
  - `last-modified`
  - `server`
  - `date`
  - `set-cookie`
- keep request and response bodies only when they remain useful to AI analysis
- apply structural JSON trimming rather than raw text truncation

## Implementation Principles

- Keep code modular: cleaners, exporters, models, CLI, config.
- Add type annotations throughout.
- Use small pure functions for rule logic.
- Prefer deterministic outputs for snapshot testing.
- Preserve extension points for future sources such as storage, accessibility trees, traces, and CDP logs.

## Delivery Order

1. project skeleton and tooling
2. HTML cleaner MVP
3. HAR cleaner MVP
4. exporter and AI context summarization
5. plugins and advanced adapters
