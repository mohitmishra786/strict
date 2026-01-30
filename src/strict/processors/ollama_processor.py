import time
import httpx
from strict.config import settings
from strict.core.interfaces import AsyncProcessor
from strict.integrity.schemas import ProcessingRequest, OutputSchema, ProcessorType
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
            except Exception as e:
                result = f"Error calling Ollama: {str(e)}"

        return await self._create_output(result, ProcessorType.LOCAL, start_time)
