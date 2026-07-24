from __future__ import annotations

from abc import ABC, abstractmethod

from xrazor.models.result import CleanResult


class Cleaner(ABC):
    @abstractmethod
    def clean(self, raw: str) -> CleanResult:
        raise NotImplementedError
