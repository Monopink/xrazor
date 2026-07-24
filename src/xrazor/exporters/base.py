from __future__ import annotations

from abc import ABC, abstractmethod

from xrazor.models.result import ExportResult


class Exporter(ABC):
    @abstractmethod
    def export(self, cleaned_content: str) -> ExportResult:
        raise NotImplementedError
