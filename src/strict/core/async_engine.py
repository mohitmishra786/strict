import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar, Type

from pydantic import BaseModel

from strict.core.math_engine import (
    validate_model_output,
    calculate_system_success_probability,
    determine_processor,
)

T = TypeVar("T", bound=BaseModel)


class AsyncMathEngine:
    """Async wrapper for the Math Engine."""

    def __init__(self, executor: ThreadPoolExecutor | None = None):
        self.executor = executor

    async def validate_model_output(
        self, raw_input: dict, schema: Type[T]
    ) -> tuple[T | None, list[str]]:
        """Async version of validate_model_output."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor, validate_model_output, raw_input, schema
        )

    async def calculate_system_success_probability(
        self,
        cloud_failure_probability: float,
        local_failure_probability: float,
        failover_enabled: bool = True,
    ) -> float:
        """Async version of system success probability."""
        # This is fast enough to run in main loop, but for consistency:
        return calculate_system_success_probability(
            cloud_failure_probability, local_failure_probability, failover_enabled
        )

    async def determine_processor(
        self, input_tokens: int, token_threshold: int = 500
    ) -> str:
        """Async version of determine_processor."""
        return determine_processor(input_tokens, token_threshold)
