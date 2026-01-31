from abc import ABC, abstractmethod
from typing import Any

from strict.integrity.schemas import ProcessingRequest, OutputSchema


class AsyncProcessor(ABC):
    """Abstract base class for async processors."""

    @abstractmethod
    async def process(self, request: ProcessingRequest) -> OutputSchema:
        """Process a request asynchronously.

        Args:
            request: Validated processing request.

        Returns:
            OutputSchema with results.
        """
        pass
