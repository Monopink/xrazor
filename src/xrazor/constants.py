from dataclasses import dataclass


@dataclass(frozen=True)
class XRazorNoteSet:
    file_note: str = (
        "This artifact was cleaned by XRazor for AI readability. "
        "Non-essential content may have been removed or simplified."
    )
    filtered_base64: str = "[xrazor]filtered-base64-content"
    removed_binary: str = "[xrazor]removed-binary-content"
    trimmed_long_text: str = "[xrazor]trimmed-long-text"
    removed_non_essential: str = "[xrazor]removed-non-essential-content"
    truncated_json: str = "[xrazor]truncated-json-value"


NOTES = XRazorNoteSet()
