from strict.core.interfaces import AsyncProcessor
from strict.integrity.schemas import (
    ProcessingRequest,
    OutputSchema,
    ValidationResult,
    ValidationStatus,
    ProcessorType,
)
import time


class BaseProcessor(AsyncProcessor):
    """Base processor with common logic."""

    async def _create_output(
        self, result: str, processor_type: ProcessorType, start_time: float
    ) -> OutputSchema:
        """Create a standardized output schema."""
        duration = (time.time() - start_time) * 1000

        return OutputSchema(
            result=result,
            validation=ValidationResult(
                status=ValidationStatus.SUCCESS,
                is_valid=True,
                input_hash="hash_placeholder",  # In real impl, compute hash
                errors=(),
                warnings=(),
            ),
            processor_used=processor_type,
            processing_time_ms=duration,
            retries_attempted=0,
        )
