from typing import Annotated, Any
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from strict.integrity.schemas import ValidationResult
from strict.processors.manager import ProcessorManager
from strict.api.schemas import (
    ProcessingRequestDTO,
    SignalConfigDTO,
    ValidationResponse,
    HealthResponse,
)
from strict.api.security import (
    Token,
    create_access_token,
    get_current_user_or_apikey,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    TokenData,
)
from strict.config import get_settings

router = APIRouter()
processor_manager = ProcessorManager()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Authenticate user and return access token."""
    settings = get_settings()

    if form_data.username != settings.admin_username or not verify_password(
        form_data.password, settings.admin_password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@router.post("/validate/signal", response_model=ValidationResponse)
async def validate_signal(
    dto: SignalConfigDTO,
    current_user: Annotated[TokenData, Depends(get_current_user_or_apikey)],
) -> ValidationResponse:
    """Validate a signal configuration.

    Requires Authentication.
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
async def process_request(
    dto: ProcessingRequestDTO,
    current_user: Annotated[TokenData, Depends(get_current_user_or_apikey)],
) -> dict[str, Any]:
    """Process a request with routing logic.

    Requires Authentication.
    """
    try:
        # Convert DTO to strict domain model
        request = dto.to_domain()

        # Process using manager (calls actual LLMs)
        output = await processor_manager.process_request(request)

        return output.model_dump()
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
