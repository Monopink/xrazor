from __future__ import annotations

import json
from typing import Any

from lxml import html

from xrazor.exporters.base import Exporter
from xrazor.models.result import ExportResult


class HtmlJsonExporter(Exporter):
    def export(self, cleaned_content: str) -> ExportResult:
        document = html.fromstring(cleaned_content)
        payload = self._to_node(document)
        return ExportResult(content=json.dumps(payload, ensure_ascii=False, indent=2), media_type="application/json")

    def _to_node(self, element: html.HtmlElement) -> dict[str, Any]:
        text = (element.text or "").strip()
        return {
            "tag": element.tag,
            "text": text,
            "attributes": dict(element.attrib),
            "children": [
                self._to_node(child)
                for child in element
                if isinstance(child.tag, str)
            ],
        }


class HtmlMarkdownExporter(Exporter):
    def export(self, cleaned_content: str) -> ExportResult:
        document = html.fromstring(cleaned_content)
        lines = self._render_node(document, depth=0)
        return ExportResult(content="\n".join(lines), media_type="text/markdown")

    def _render_node(self, element: html.HtmlElement, *, depth: int) -> list[str]:
        indent = "  " * depth
        text = (element.text or "").strip()
        attrs = " ".join(f'{key}="{value}"' for key, value in element.attrib.items())
        header = f"{indent}- <{element.tag}{(' ' + attrs) if attrs else ''}>"
        if text:
            header += f" {text}"

        lines = [header]
        for child in element:
            if isinstance(child.tag, str):
                lines.extend(self._render_node(child, depth=depth + 1))
        return lines
