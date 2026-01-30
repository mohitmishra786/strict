import pytest
from pydantic import BaseModel, ConfigDict

from strict.core.async_engine import AsyncMathEngine


class SimpleModel(BaseModel):
    model_config = ConfigDict(strict=True)
    value: int


@pytest.mark.asyncio
async def test_async_validate_model_output():
    engine = AsyncMathEngine()
    result, errors = await engine.validate_model_output({"value": 10}, SimpleModel)
    assert result is not None
    assert result.value == 10
    assert errors == []


@pytest.mark.asyncio
async def test_async_calculate_probability():
    engine = AsyncMathEngine()
    prob = await engine.calculate_system_success_probability(0.1, 0.1)
    assert prob == 0.99
