from __future__ import annotations

import json
from typing import Any

from xrazor.exporters.base import Exporter
from xrazor.models.result import ExportResult


class HarMarkdownExporter(Exporter):
    def export(self, cleaned_content: str) -> ExportResult:
        data = json.loads(cleaned_content)
        entries = data.get("log", {}).get("entries", [])
        lines = ["# XRazor HAR Summary", ""]
        for entry in entries:
            request = entry.get("request", {})
            response = entry.get("response", {})
            lines.append(
                f"- `{request.get('method', 'GET')}` {request.get('url', '')} -> {response.get('status', '')}"
            )
        return ExportResult(content="\n".join(lines), media_type="text/markdown")


class HarJsonExporter(Exporter):
    def export(self, cleaned_content: str) -> ExportResult:
        data: dict[str, Any] = json.loads(cleaned_content)
        return ExportResult(content=json.dumps(data, ensure_ascii=False, indent=2), media_type="application/json")
