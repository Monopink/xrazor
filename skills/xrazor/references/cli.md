# XRazor CLI Reference

Use these commands from the XRazor project root.

## Core Commands

```powershell
python -m xrazor clean <input> [--out <output>] [--kind html|har]
python -m xrazor export <input> --format json|markdown [--out <output>] [--kind html|har]
python -m xrazor context <input> [--out <output>] [--kind html|har]
```

## HTML-Specific Overrides

```powershell
python -m xrazor clean page.html --image-mode remove
python -m xrazor clean page.html --image-mode strip-base64
python -m xrazor clean page.html --class-mode none
python -m xrazor clean page.html --class-mode semantic
python -m xrazor clean page.html --class-mode all
```

## Output Intents

- `clean`: produce a transformed artifact
- `export`: produce structured JSON or markdown
- `context`: produce a compact AI-facing summary
