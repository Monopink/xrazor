from __future__ import annotations

import re
from collections.abc import Iterable

from lxml import etree, html

from xrazor.cleaners.base import Cleaner
from xrazor.constants import NOTES
from xrazor.models.config import HtmlCleanerConfig
from xrazor.models.result import CleanResult

WHITESPACE_RE = re.compile(r"\s+")
HASH_CLASS_RE = re.compile(r"^(?:[a-f0-9]{6,}|[A-Za-z0-9_-]{12,})$")
EVENT_ATTR_RE = re.compile(r"^on[a-z]+$")
GENERATED_CLASS_PATTERNS = (
    re.compile(r"^css-"),
    re.compile(r"^e[a-z0-9]{6,}$"),
    re.compile(r"^[a-z]{2,}\d[a-z0-9]{3,}$"),
    re.compile(r".*_v\d+(?:_\d+)*$"),
)
SEMANTIC_CLASS_SEGMENT_RE = re.compile(r"^[A-Za-z][A-Za-z-]{2,}$")
CLASS_STOPWORDS = {
    "active",
    "base",
    "box",
    "canary",
    "card",
    "center",
    "component",
    "container",
    "content",
    "default",
    "element",
    "item",
    "label",
    "left",
    "medium",
    "primary",
    "right",
    "small",
    "text",
    "tiny",
    "top",
    "wrapper",
}


class HtmlCleaner(Cleaner):
    def __init__(self, config: HtmlCleanerConfig | None = None) -> None:
        self.config = config or HtmlCleanerConfig()

    def clean(self, raw: str) -> CleanResult:
        parser = html.HTMLParser(remove_comments=False, encoding="utf-8")
        document = html.fromstring(raw, parser=parser)
        warnings: list[str] = []

        self._remove_comments(document)
        self._remove_tags(document, self.config.remove_tags)
        self._clean_attributes(document)
        self._normalize_text_nodes(document)
        if self.config.remove_empty_nodes:
            self._remove_empty_nodes(document)

        cleaned = html.tostring(document, encoding="unicode", method="html")
        note = f"<!-- XRazor: {NOTES.file_note} -->\n"
        return CleanResult(content=note + cleaned, warnings=warnings)

    def _remove_comments(self, document: html.HtmlElement) -> None:
        for node in document.xpath("//comment()"):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)

    def _remove_tags(self, document: html.HtmlElement, tag_names: Iterable[str]) -> None:
        xpath = " | ".join(f"//{tag_name}" for tag_name in tag_names)
        if not xpath:
            return
        for node in document.xpath(xpath):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)

    def _clean_attributes(self, document: html.HtmlElement) -> None:
        for element in document.iter():
            if not isinstance(element.tag, str):
                continue

            original_attributes = dict(element.attrib)
            element.attrib.clear()

            for name, value in original_attributes.items():
                lowered = name.lower()
                if EVENT_ATTR_RE.match(lowered):
                    continue
                if lowered in {"style", "tabindex", "draggable", "contenteditable"}:
                    continue
                if lowered == "class":
                    cleaned_class = self._filter_class_value(value)
                    if cleaned_class:
                        element.attrib["class"] = cleaned_class
                    continue
                if lowered.startswith("aria-") and lowered not in self.config.keep_aria_attributes:
                    continue
                if lowered in self.config.keep_aria_attributes:
                    element.attrib[name] = self._truncate_attribute_value(value)
                    continue
                if lowered.startswith("data-") and lowered not in self.config.keep_data_attributes:
                    continue
                if lowered in self.config.keep_data_attributes:
                    element.attrib[name] = self._truncate_attribute_value(value)
                    continue
                if lowered not in self.config.keep_attributes:
                    continue
                if lowered == "src":
                    value = self._clean_src_value(value)
                element.attrib[name] = self._truncate_attribute_value(value)

    def _filter_class_value(self, value: str) -> str:
        if not self.config.keep_semantic_class_names:
            return ""

        kept = [token for token in value.split() if self._is_semantic_class_token(token)]
        return " ".join(kept)

    def _is_semantic_class_token(self, token: str) -> bool:
        lowered = token.lower()
        if any(pattern.match(token) for pattern in GENERATED_CLASS_PATTERNS):
            return False
        if HASH_CLASS_RE.match(token) and "-" not in token and "_" not in token:
            return False
        if lowered.startswith("tux-"):
            return False

        segments = [segment for segment in re.split(r"[-_]", token) if segment]
        semantic_segments = [
            segment
            for segment in segments
            if SEMANTIC_CLASS_SEGMENT_RE.match(segment)
            and segment.lower() not in CLASS_STOPWORDS
        ]
        return bool(semantic_segments)

    def _clean_src_value(self, value: str) -> str:
        if value.startswith("data:"):
            return NOTES.filtered_base64
        if not self.config.preserve_img_src:
            return NOTES.removed_non_essential
        return value

    def _truncate_attribute_value(self, value: str) -> str:
        if len(value) <= self.config.max_attribute_value_length:
            return value
        return NOTES.trimmed_long_text

    def _normalize_text_nodes(self, document: html.HtmlElement) -> None:
        for element in document.iter():
            if element.text:
                element.text = self._normalize_text(element.text)
            if element.tail:
                element.tail = self._normalize_text(element.tail)

    def _normalize_text(self, value: str) -> str:
        normalized = WHITESPACE_RE.sub(" ", value).strip()
        return normalized

    def _remove_empty_nodes(self, document: html.HtmlElement) -> None:
        changed = True
        while changed:
            changed = False
            for element in list(document.iterdescendants()):
                if not isinstance(element.tag, str):
                    continue
                if self._should_keep_empty_node(element):
                    continue
                text = (element.text or "").strip()
                if text or len(element):
                    continue
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)
                    changed = True

    def _should_keep_empty_node(self, element: html.HtmlElement) -> bool:
        if element.tag in {"input", "button", "a", "form", "label", "img"}:
            return True
        return any(key in element.attrib for key in {"id", "name", "href", "value", "role", "type"})
