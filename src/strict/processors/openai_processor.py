import time
from typing import Any

from openai import AsyncOpenAI
from strict.config import settings
from strict.core.interfaces import AsyncProcessor
from strict.integrity.schemas import ProcessingRequest, OutputSchema, ProcessorType
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                # In production, we might want to limit tokens based on request
            )
            result = response.choices[0].message.content or ""
        except Exception as e:
            # For now, return error as result, or raise exception to be handled by caller
            # Ideally we return a failed ValidationResult
            result = f"Error calling OpenAI: {str(e)}"
            # In a robust system we would handle retry logic here or in base class

        return await self._create_output(result, ProcessorType.CLOUD, start_time)
