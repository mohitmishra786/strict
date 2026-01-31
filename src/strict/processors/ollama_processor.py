import time
import json
from typing import AsyncGenerator
import httpx
from strict.config import settings
from strict.core.interfaces import AsyncProcessor
from strict.integrity.schemas import (
    ProcessingRequest,
    OutputSchema,
    ProcessorType,
    ValidationResult,
    ValidationStatus,
)
from strict.processors.base import BaseProcessor


class OllamaProcessor(BaseProcessor):
    """Processor using Ollama (Local)."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = "llama3"  # Default local model

    async def process(self, request: ProcessingRequest) -> OutputSchema:
        """Process request using Ollama."""
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": request.input_data,
                        "stream": False,
                    },
                    timeout=request.timeout_seconds,
                )
                response.raise_for_status()
                result = response.json().get("response", "")
            except (
                httpx.HTTPStatusError,
                httpx.TimeoutException,
                httpx.ConnectError,
                json.JSONDecodeError,
            ) as e:
                duration = (time.time() - start_time) * 1000
                return OutputSchema(
                    result="",
                    validation=ValidationResult(
                        status=ValidationStatus.FAILURE,
                        is_valid=False,
                        input_hash="hash_placeholder",
                        errors=(f"Ollama error: {str(e)}",),
                        warnings=(),
                    ),
                    processor_used=ProcessorType.LOCAL,
                    processing_time_ms=duration,
                    retries_attempted=0,
                )

        return await self._create_output(result, ProcessorType.LOCAL, start_time)

    async def stream_process(
        self, request: ProcessingRequest
    ) -> AsyncGenerator[str, None]:
        """Stream processing using Ollama."""
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": request.input_data,
                        "stream": True,
                    },
                    timeout=request.timeout_seconds,
                ) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done"):
                            break
            except Exception:
                yield "Error during streaming"
