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
        entries = data.get("log", {}).get("entries", [])
        cleaned_entries = []
        warnings: list[str] = []

        for entry in entries:
            if not self._should_keep_entry(entry):
                continue
            cleaned_entries.append(self._clean_entry(entry))

        if "log" in data:
            data["log"]["entries"] = cleaned_entries
        data["_xrazor_note"] = NOTES.file_note
        return CleanResult(content=json.dumps(data, ensure_ascii=False, indent=2), warnings=warnings)

    def _should_keep_entry(self, entry: dict[str, Any]) -> bool:
        resource_type = str(entry.get("_resourceType", "")).lower()
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

        request["headers"] = self._clean_headers(request.get("headers", []), is_response=False)
        response["headers"] = self._clean_headers(response.get("headers", []), is_response=True)

        if self.config.remove_cookie_headers:
            request.pop("cookies", None)
        if self.config.remove_response_cookies:
            response.pop("cookies", None)

        entry.pop("cache", None)
        entry.pop("timings", None)
        entry.pop("serverIPAddress", None)
        entry.pop("connection", None)
        entry.pop("_securityDetails", None)
        entry.pop("_webSocketMessages", None)

        if "postData" in request:
            request["postData"] = self._clean_post_data(request["postData"])
        if "content" in response:
            response["content"] = self._clean_content(response["content"])

        entry["request"] = request
        entry["response"] = response
        return entry

    def _clean_headers(self, headers: list[dict[str, Any]], *, is_response: bool) -> list[dict[str, Any]]:
        cleaned = []
        for header in headers:
            name = str(header.get("name", "")).lower()
            if name.startswith("sec-ch-") or name.startswith("sec-fetch-"):
                continue
            if is_response and name in RESPONSE_HEADERS_TO_DROP:
                continue
            if not is_response and name in REQUEST_HEADERS_TO_DROP:
                continue
            cleaned.append(header)
        return cleaned

    def _clean_post_data(self, post_data: dict[str, Any]) -> dict[str, Any]:
        text = post_data.get("text")
        if not isinstance(text, str):
            return post_data

        mime_type = str(post_data.get("mimeType", ""))
        if "json" in mime_type:
            post_data["text"] = self._trim_json_text(text)
            return post_data

        if len(text) > self.config.trim_long_strings_to:
            post_data["text"] = NOTES.trimmed_long_text
        return post_data

    def _clean_content(self, content: dict[str, Any]) -> dict[str, Any]:
        mime_type = str(content.get("mimeType", "")).lower()
        text = content.get("text")

        if mime_type.startswith(("image/", "font/", "video/", "audio/")):
            content["text"] = NOTES.removed_binary
            content["encoding"] = "xrazor"
            return content

        if isinstance(text, str):
            if "json" in mime_type:
                content["text"] = self._trim_json_text(text)
            elif self._looks_like_base64(text):
                content["text"] = NOTES.filtered_base64
            elif len(text) > self.config.trim_long_strings_to:
                content["text"] = NOTES.trimmed_long_text
        return content

    def _trim_json_text(self, raw_json: str) -> str:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            return NOTES.truncated_json if len(raw_json) > self.config.trim_long_strings_to else raw_json
        trimmed = self._trim_json_value(payload, depth=0)
        return json.dumps(trimmed, ensure_ascii=False)

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

    def _looks_like_base64(self, value: str) -> bool:
        if len(value) < 256:
            return False
        return not any(ch in value for ch in "{[< \n\t")
