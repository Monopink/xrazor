from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CleanResult:
    content: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExportResult:
    content: str
    media_type: str


@dataclass
class ContextSection:
    title: str
    lines: list[str]
