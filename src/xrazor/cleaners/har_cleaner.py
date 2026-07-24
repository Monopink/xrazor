from __future__ import annotations

import json
from typing import Any

from xrazor.cleaners.base import Cleaner
from xrazor.constants import NOTES
from xrazor.models.config import HarCleanerConfig
from xrazor.models.result import CleanResult

REQUEST_HEADERS_TO_DROP = {
    "accept-encoding",
    "accept-language",
    "priority",
    "cookie",
}
RESPONSE_HEADERS_TO_DROP = {
    "etag",
    "expires",
    "last-modified",
    "server",
    "date",
    "set-cookie",
}


class HarCleaner(Cleaner):
    def __init__(self, config: HarCleanerConfig | None = None) -> None:
        self.config = config or HarCleanerConfig()

    def clean(self, raw: str) -> CleanResult:
        data = json.loads(raw)
        log = data.get("log", {})
        entries = log.get("entries", [])
        cleaned_entries = []
        warnings: list[str] = []

        for entry in entries:
            if not self._should_keep_entry(entry):
                continue
            cleaned_entries.append(self._clean_entry(entry))

        cleaned_payload = {
            "_xrazor_note": NOTES.file_note,
            "log": {
                "pages": self._clean_pages(log.get("pages", [])),
                "entries": cleaned_entries,
            },
        }
        return CleanResult(
            content=json.dumps(cleaned_payload, ensure_ascii=False, indent=2), warnings=warnings
        )

    def _should_keep_entry(self, entry: dict[str, Any]) -> bool:
        resource_type = self._resource_type_for_entry(entry)
        if resource_type in self.config.keep_resource_types:
            return True
        if resource_type in self.config.drop_resource_types:
            return False

        mime_type = self._extract_mime_type(entry)
        if mime_type.startswith(("image/", "font/", "video/", "audio/")):
            return False
        return mime_type.startswith(("application/json", "text/html", "text/plain"))

    def _clean_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        request = entry.get("request", {})
        response = entry.get("response", {})
        cleaned_entry: dict[str, Any] = {
            "_resourceType": self._resource_type_for_entry(entry),
            "request": {
                "method": request.get("method", "GET"),
                "url": request.get("url", ""),
            },
            "response": {
                "status": response.get("status", ""),
            },
        }

        query = self._clean_query_string(request.get("queryString", []))
        if query:
            cleaned_entry["request"]["query"] = query

        headers = self._clean_headers(request.get("headers", []), is_response=False)
        if headers:
            cleaned_entry["request"]["headers"] = headers

        response_headers = self._clean_headers(response.get("headers", []), is_response=True)
        if response_headers:
            cleaned_entry["response"]["headers"] = response_headers

        if "postData" in request:
            cleaned_post_data = self._clean_post_data(request["postData"])
            if cleaned_post_data:
                cleaned_entry["request"]["postData"] = cleaned_post_data

        if "content" in response:
            cleaned_content = self._clean_content(response["content"])
            if cleaned_content:
                cleaned_entry["response"]["content"] = cleaned_content

        return cleaned_entry

    def _clean_pages(self, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cleaned_pages: list[dict[str, Any]] = []
        for page in pages:
            cleaned_page: dict[str, Any] = {}
            if page.get("id"):
                cleaned_page["id"] = page["id"]
            if page.get("title"):
                cleaned_page["title"] = page["title"]
            if cleaned_page:
                cleaned_pages.append(cleaned_page)
        return cleaned_pages

    def _clean_headers(self, headers: list[dict[str, Any]], *, is_response: bool) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for header in headers:
            name = str(header.get("name", "")).lower()
            if name.startswith("sec-ch-") or name.startswith("sec-fetch-"):
                continue
            if is_response and name in RESPONSE_HEADERS_TO_DROP:
                continue
            if not is_response and name in REQUEST_HEADERS_TO_DROP:
                continue
            if name.startswith(":"):
                continue
            cleaned[name] = str(header.get("value", ""))
        return cleaned

    def _clean_query_string(self, query_string: list[dict[str, Any]]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for item in query_string:
            name = str(item.get("name", ""))
            if not name:
                continue
            cleaned[name] = str(item.get("value", ""))
        return cleaned

    def _clean_post_data(self, post_data: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        mime_type = str(post_data.get("mimeType", ""))
        if mime_type:
            cleaned["mimeType"] = mime_type

        params = post_data.get("params")
        if isinstance(params, list) and params:
            cleaned["params"] = [
                {"name": str(param.get("name", "")), "value": str(param.get("value", ""))}
                for param in params
                if param.get("name")
            ]

        text = post_data.get("text")
        if not isinstance(text, str):
            return cleaned

        if "json" in mime_type:
            cleaned_json = self._trim_json_value_or_text(text)
            cleaned["json"] = cleaned_json
            return cleaned

        if len(text) > self.config.trim_long_strings_to:
            cleaned["text"] = NOTES.trimmed_long_text
        else:
            cleaned["text"] = text
        return cleaned

    def _clean_content(self, content: dict[str, Any]) -> dict[str, Any]:
        mime_type = str(content.get("mimeType", "")).lower()
        cleaned: dict[str, Any] = {}
        if mime_type:
            cleaned["mimeType"] = mime_type
        text = content.get("text")

        if mime_type.startswith(("image/", "font/", "video/", "audio/")):
            cleaned["text"] = NOTES.removed_binary
            return cleaned

        if isinstance(text, str):
            if "json" in mime_type:
                cleaned["json"] = self._trim_json_value_or_text(text)
            elif self._looks_like_base64(text):
                cleaned["text"] = NOTES.filtered_base64
            elif len(text) > self.config.trim_long_strings_to:
                cleaned["text"] = NOTES.trimmed_long_text
            else:
                cleaned["text"] = text
        return cleaned

    def _trim_json_value_or_text(self, raw_json: str) -> Any:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            return NOTES.truncated_json if len(raw_json) > self.config.trim_long_strings_to else raw_json
        return self._trim_json_value(payload, depth=0)

    def _trim_json_value(self, value: Any, *, depth: int) -> Any:
        if depth >= self.config.max_json_depth:
            return NOTES.truncated_json

        if isinstance(value, dict):
            items = list(value.items())[: self.config.trim_json_object_keys_to]
            trimmed_dict = {
                key: self._trim_json_value(inner_value, depth=depth + 1)
                for key, inner_value in items
            }
            if len(value) > len(items):
                trimmed_dict["_xrazor"] = {
                    "message": NOTES.truncated_json,
                    "original_key_count": len(value),
                    "kept_key_count": len(items),
                }
            return trimmed_dict

        if isinstance(value, list):
            items = value[: self.config.trim_json_arrays_to]
            trimmed_list = [self._trim_json_value(item, depth=depth + 1) for item in items]
            if len(value) > len(items):
                trimmed_list.append(
                    {
                        "_xrazor": {
                            "message": NOTES.truncated_json,
                            "original_item_count": len(value),
                            "kept_item_count": len(items),
                        }
                    }
                )
            return trimmed_list

        if isinstance(value, str) and len(value) > self.config.trim_long_strings_to:
            return NOTES.trimmed_long_text

        return value

    def _extract_mime_type(self, entry: dict[str, Any]) -> str:
        content = entry.get("response", {}).get("content", {})
        mime_type = str(content.get("mimeType", "")).lower()
        if mime_type:
            return mime_type

        for header in entry.get("response", {}).get("headers", []):
            if str(header.get("name", "")).lower() == "content-type":
                return str(header.get("value", "")).lower()
        return ""

    def _resource_type_for_entry(self, entry: dict[str, Any]) -> str:
        explicit = str(entry.get("_resourceType", "")).lower().strip()
        if explicit:
            return explicit

        mime_type = self._extract_mime_type(entry)
        request = entry.get("request", {})
        response = entry.get("response", {})
        method = str(request.get("method", "GET")).upper()
        url = str(request.get("url", "")).lower()
        status = int(response.get("status", 0) or 0)

        if mime_type.startswith("text/html"):
            return "document"
        if mime_type.startswith("application/json") or "/api/" in url:
            return "xhr"
        if mime_type.startswith(("image/", "font/", "video/", "audio/")):
            return "binary"
        if mime_type.startswith("text/css"):
            return "stylesheet"
        if "javascript" in mime_type:
            return "script"
        if method in {"POST", "PUT", "PATCH", "DELETE"} and status >= 0:
            return "fetch"
        return "other"

    def _looks_like_base64(self, value: str) -> bool:
        if len(value) < 256:
            return False
        return not any(ch in value for ch in "{[< \n\t")
