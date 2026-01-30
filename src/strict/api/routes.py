from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from strict.integrity.schemas import ValidationResult
from strict.processors.manager import ProcessorManager
from strict.api.schemas import (
    ProcessingRequestDTO,
    SignalConfigDTO,
    ValidationResponse,
    HealthResponse,
)

router = APIRouter()
processor_manager = ProcessorManager()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@router.post("/validate/signal", response_model=ValidationResponse)
async def validate_signal(dto: SignalConfigDTO) -> ValidationResponse:
    """Validate a signal configuration.

    Accepts loose JSON input, parses it, and attempts to construct
    the strict SignalConfig domain model.
    """
    try:
        # Attempt to create the strict domain model
        result = dto.to_domain()

        return ValidationResponse(
            valid=True,
            errors=[],
            validated_data=result.model_dump(),
        )
    except ValidationError as e:
        # Collect structured errors
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return ValidationResponse(
            valid=False,
            errors=errors,
            validated_data=None,
        )
    except ValueError as e:
        # Handle business logic errors (like Nyquist violation)
        return ValidationResponse(
            valid=False,
            errors=[str(e)],
            validated_data=None,
        )


@router.post("/process/request")
async def process_request(dto: ProcessingRequestDTO) -> dict[str, Any]:
    """Process a request with routing logic."""
    try:
        # Convert DTO to strict domain model
        request = dto.to_domain()

        # Process using manager (calls actual LLMs)
        output = await processor_manager.process_request(request)

        return output.model_dump()
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
