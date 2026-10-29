from __future__ import annotations

import json
from pathlib import Path

import pytest

from xrazor.cleaners.har_cleaner import HarCleaner
from xrazor.cleaners.html_cleaner import HtmlCleaner


REPO_ROOT = Path(__file__).resolve().parents[1]


def sample_path(name: str) -> Path:
    for candidate in (
        REPO_ROOT / name,
        REPO_ROOT / "ref" / name,
        REPO_ROOT / "tests" / "fixtures" / name,
    ):
        if candidate.exists():
            return candidate
    raise AssertionError(f"Missing integration sample: {name}")


@pytest.mark.integration
def test_sample_html_cleaning_preserves_title_and_removes_script() -> None:
    raw = sample_path("tt_page.html").read_text(encoding="utf-8")

    result = HtmlCleaner().clean(raw)

    assert "Ms.Vi" in result.content
    assert "<script" not in result.content.lower()
    assert "<style" not in result.content.lower()
    assert "XRazor" in result.content


@pytest.mark.integration
def test_sample_har_cleaning_keeps_document_or_api_entries() -> None:
    raw = sample_path("item_list.har").read_text(encoding="utf-8")

    result = HarCleaner().clean(raw)
    cleaned = json.loads(result.content)
    entries = cleaned["log"]["entries"]

    assert entries
    assert all(entry.get("_resourceType") in {"document", "xhr", "fetch", "other", "ping"} for entry in entries)
    assert cleaned["_xrazor_note"]
    assert "creator" not in cleaned["log"]
    assert "version" not in cleaned["log"]


@pytest.mark.integration
def test_firefox_single_api_har_is_supported() -> None:
    raw = sample_path("api_post_item_list.har").read_text(encoding="utf-8")

    result = HarCleaner().clean(raw)
    cleaned = json.loads(result.content)
    entries = cleaned["log"]["entries"]

    assert len(entries) == 1
    assert entries[0]["_resourceType"] == "xhr"
    assert "/api/post/item_list/" in entries[0]["request"]["url"]
