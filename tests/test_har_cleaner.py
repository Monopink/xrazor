from __future__ import annotations

import json

from xrazor.cleaners.har_cleaner import HarCleaner


def test_har_cleaner_drops_script_entries_and_keeps_xhr() -> None:
    cleaner = HarCleaner()
    raw = json.dumps(
        {
            "log": {
                "entries": [
                    {
                        "_resourceType": "script",
                        "request": {"method": "GET", "url": "https://example.com/app.js", "headers": []},
                        "response": {"status": 200, "headers": [], "content": {"mimeType": "application/javascript"}},
                    },
                    {
                        "_resourceType": "xhr",
                        "request": {"method": "GET", "url": "https://example.com/api", "headers": []},
                        "response": {
                            "status": 200,
                            "headers": [],
                            "content": {"mimeType": "application/json", "text": "{\"ok\":true}"},
                        },
                    },
                ]
            }
        }
    )

    result = cleaner.clean(raw)
    cleaned = json.loads(result.content)
    entries = cleaned["log"]["entries"]
    assert len(entries) == 1
    assert entries[0]["request"]["url"] == "https://example.com/api"

