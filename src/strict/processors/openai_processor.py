import time
from typing import Any

from openai import AsyncOpenAI, APIError
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


class OpenAIProcessor(BaseProcessor):
    """Processor using OpenAI API."""

    def __init__(self):
        api_key = (
            settings.openai_api_key.get_secret_value()
            if settings.openai_api_key
            else None
        )
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Default model

    async def process(self, request: ProcessingRequest) -> OutputSchema:
        """Process request using OpenAI."""
        start_time = time.time()

        # In a real scenario, we'd use the input_data to construct messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": request.input_data},
        ]

        try:
            # Use client with timeout from request
            client_with_timeout = self.client.with_options(
                timeout=request.timeout_seconds
            )
            response = await client_with_timeout.chat.completions.create(
                model=self.model,
                messages=messages,
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
                    errors=(f"OpenAI API error: {str(e)}",),
                    warnings=(),
                ),
                processor_used=ProcessorType.CLOUD,
                processing_time_ms=duration,
                retries_attempted=0,
            )

        return await self._create_output(result, ProcessorType.CLOUD, start_time)
