from __future__ import annotations

import json
from collections import Counter
from urllib.parse import urlparse
from typing import Any

from lxml import html

from xrazor.models.result import ExportResult

GENERIC_LABELS = {"a", "button", "div", "i", "img", "input", "span"}
NOISE_HOST_KEYWORDS = ("monitor", "mcs-", "mssdk", "mon.", "mon-", "webcast")
NOISE_PATH_KEYWORDS = ("/report/", "/monitor_", "/privacy_headers", "/collect/", "/settings/browser-settings")


class HtmlAiContextExporter:
    def export(self, cleaned_content: str) -> ExportResult:
        document = html.document_fromstring(cleaned_content)
        title = self._first_text(document.xpath("//title/text()"))
        headings = self._collect_headings(document)
        stats = self._collect_stats(document)
        buttons = self._collect_elements(document, "//button | //*[@role='button']")
        links = self._collect_elements(document, "//a[@href]")
        inputs = self._collect_inputs(document)

        lines = ["# XRazor HTML Context", ""]
        if title:
            lines.extend(["Page title:", title, ""])
        if headings:
            lines.append("Important headings:")
            lines.extend(f"- {item}" for item in headings[:12])
            lines.append("")
        if stats:
            lines.append("Visible stats:")
            lines.extend(f"- {item}" for item in stats[:12])
            lines.append("")
        if buttons:
            lines.append("Important buttons:")
            lines.extend(f"- {item}" for item in buttons[:20])
            lines.append("")
        if inputs:
            lines.append("Inputs:")
            lines.extend(f"- {item}" for item in inputs[:20])
            lines.append("")
        if links:
            lines.append("Links:")
            lines.extend(f"- {item}" for item in links[:20])
        return ExportResult(content="\n".join(lines).strip(), media_type="text/markdown")

    def _collect_elements(self, document: html.HtmlElement, xpath: str) -> list[str]:
        results: list[str] = []
        for element in document.xpath(xpath):
            if not isinstance(element.tag, str):
                continue
            text = " ".join(part.strip() for part in element.itertext() if part.strip())
            label = (
                text
                or element.attrib.get("aria-label")
                or element.attrib.get("title")
                or element.attrib.get("data-e2e")
                or element.attrib.get("data-testid")
                or element.tag
            )
            label = label.strip()
            if not label or label.lower() in GENERIC_LABELS:
                continue
            results.append(label)
        return self._dedupe_preserve_order(results)

    def _collect_inputs(self, document: html.HtmlElement) -> list[str]:
        results: list[str] = []
        for element in document.xpath("//input | //textarea | //select"):
            if not isinstance(element.tag, str):
                continue
            label = (
                element.attrib.get("placeholder")
                or element.attrib.get("name")
                or element.attrib.get("id")
                or element.attrib.get("type")
                or element.tag
            )
            results.append(label)
        return self._dedupe_preserve_order(results)

    def _collect_headings(self, document: html.HtmlElement) -> list[str]:
        results: list[str] = []
        for element in document.xpath("//h1 | //h2 | //h3"):
            text = " ".join(part.strip() for part in element.itertext() if part.strip())
            if text and text.lower() not in GENERIC_LABELS:
                results.append(text)
        return self._dedupe_preserve_order(results)

    def _collect_stats(self, document: html.HtmlElement) -> list[str]:
        results: list[str] = []
        for element in document.xpath("//*[@data-e2e]"):
            key = element.attrib.get("data-e2e", "")
            if not key.endswith("-count"):
                continue
            value = " ".join(part.strip() for part in element.itertext() if part.strip())
            if not value:
                continue
            label = key.removesuffix("-count").replace("-", " ")
            results.append(f"{label}: {value}")
        return self._dedupe_preserve_order(results)

    def _first_text(self, values: list[str]) -> str:
        for value in values:
            value = value.strip()
            if value:
                return value
        return ""

    def _dedupe_preserve_order(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped


class HarAiContextExporter:
    def export(self, cleaned_content: str) -> ExportResult:
        data = json.loads(cleaned_content)
        entries = data.get("log", {}).get("entries", [])

        lines = ["# XRazor HAR Context", ""]
        lines.extend(self._resource_summary(entries))
        lines.append("")
        lines.append("Important APIs:")
        lines.extend(self._api_lines(entries))
        return ExportResult(content="\n".join(lines).strip(), media_type="text/markdown")

    def _resource_summary(self, entries: list[dict[str, Any]]) -> list[str]:
        counter = Counter(str(entry.get("_resourceType", "unknown")) for entry in entries)
        lines = ["Network summary:"]
        for resource_type, count in counter.most_common():
            lines.append(f"- {resource_type}: {count}")
        return lines

    def _api_lines(self, entries: list[dict[str, Any]]) -> list[str]:
        lines: list[str] = []
        seen: set[tuple[str, str]] = set()
        prioritized = sorted(entries, key=self._entry_priority, reverse=True)
        for entry in prioritized:
            request = entry.get("request", {})
            response = entry.get("response", {})
            url = str(request.get("url", ""))
            method = str(request.get("method", "GET"))
            status = response.get("status", "")
            mime_type = str(response.get("content", {}).get("mimeType", ""))
            if not self._is_useful_api(url=url, mime_type=mime_type):
                continue
            normalized = self._normalize_url(url)
            key = (method, normalized)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"- `{method}` {normalized} -> {status} ({mime_type})")
            if len(lines) >= 25:
                break
        if not lines:
            lines.append("- No high-signal API calls identified")
        return lines

    def _entry_priority(self, entry: dict[str, Any]) -> tuple[int, int, int]:
        request = entry.get("request", {})
        response = entry.get("response", {})
        url = str(request.get("url", ""))
        mime_type = str(response.get("content", {}).get("mimeType", ""))
        parsed = urlparse(url)
        path = parsed.path.lower()
        host = parsed.netloc.lower()

        first_party_score = 3 if "tiktok.com" in host else 1
        api_score = 3 if "/api/" in path else 2 if mime_type.startswith("application/json") else 1
        path_score = 2 if any(token in path for token in ("/item_list", "/playlist", "/user/", "/graphql")) else 0
        return (first_party_score, api_score, path_score)

    def _is_useful_api(self, *, url: str, mime_type: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()

        if any(keyword in path for keyword in NOISE_PATH_KEYWORDS):
            return False
        if mime_type.startswith("application/json"):
            return (not any(keyword in host for keyword in NOISE_HOST_KEYWORDS)) or "/api/" in path
        return mime_type == "text/html"

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or "/"
        if parsed.query:
            keys = sorted({item.split("=", 1)[0] for item in parsed.query.split("&") if item})
            preview = ", ".join(keys[:6])
            suffix = ", ..." if len(keys) > 6 else ""
            return f"{parsed.scheme}://{parsed.netloc}{path} ? {preview}{suffix}"
        return f"{parsed.scheme}://{parsed.netloc}{path}"
