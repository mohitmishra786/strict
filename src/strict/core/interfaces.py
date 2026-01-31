from abc import ABC, abstractmethod
from typing import AsyncGenerator

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

    async def stream_process(
        self, request: ProcessingRequest
    ) -> AsyncGenerator[str, None]:
        """Stream processing results.

        Default implementation just yields the full result from process.
        Subclasses should override this for true streaming.
        """
        result = await self.process(request)
        yield result.result
