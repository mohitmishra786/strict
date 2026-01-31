import time
from typing import Any, AsyncGenerator

from groq import AsyncGroq, APIError
from strict.config import settings
from strict.integrity.schemas import (
    ProcessingRequest,
    OutputSchema,
    ProcessorType,
    ValidationResult,
    ValidationStatus,
)
from strict.processors.base import BaseProcessor


class GroqProcessor(BaseProcessor):
    """Processor using Groq API."""

    def __init__(self):
        api_key = (
            settings.groq_api_key.get_secret_value() if settings.groq_api_key else None
        )
        if not api_key:
            if settings.allow_dummy_key or settings.debug:
                api_key = "dummy-key"
            else:
                raise ValueError("Groq API key is missing. Set STRICT_GROQ_API_KEY.")
        self.client = AsyncGroq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"  # Default model

    async def process(self, request: ProcessingRequest) -> OutputSchema:
        """Process request using Groq."""
        start_time = time.time()

        messages = [
            {
                "role": "system",
                "content": "You are a high-integrity processing engine.",
            },
            {"role": "user", "content": request.input_data},
        ]

        try:
            # Groq async client
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                timeout=request.timeout_seconds,
            )
            result = response.choices[0].message.content or ""
        except APIError as e:
            # Return failed ValidationResult for API errors
            duration = (time.time() - start_time) * 1000
            return OutputSchema(
                result="",
                validation=ValidationResult(
                    status=ValidationStatus.FAILURE,
                    is_valid=False,
                    input_hash="hash_placeholder",
                    errors=(f"Groq API error: {str(e)}",),
                    warnings=(),
                ),
                processor_used=ProcessorType.CLOUD,
                processing_time_ms=duration,
                retries_attempted=0,
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return OutputSchema(
                result="",
                validation=ValidationResult(
                    status=ValidationStatus.FAILURE,
                    is_valid=False,
                    input_hash="hash_placeholder",
                    errors=(f"Internal error: {str(e)}",),
                    warnings=(),
                ),
                processor_used=ProcessorType.CLOUD,
                processing_time_ms=duration,
                retries_attempted=0,
            )

        return await self._create_output(result, ProcessorType.CLOUD, start_time)

    async def stream_process(
        self, request: ProcessingRequest
    ) -> AsyncGenerator[str, None]:
        """Stream processing using Groq."""
        messages = [
            {
                "role": "system",
                "content": "You are a high-integrity processing engine.",
            },
            {"role": "user", "content": request.input_data},
        ]

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                stream=True,
                timeout=request.timeout_seconds,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APIError as e:
            yield f"Groq streaming error: {str(e)}"
        except Exception as e:
            yield f"Internal streaming error: {str(e)}"
