import strawberry
from enum import Enum
from typing import List, Optional, Any, AsyncGenerator
from strawberry.types import Info
from strawberry.fastapi import GraphQLRouter

from strict.integrity.schemas import (
    SignalType,
    ProcessorType,
    ValidationStatus,
    SignalConfig,
    ProcessingRequest,
)
from strict.processors.manager import ProcessorManager

# -----------------------------------------------------------------------------
# GraphQL Types
# -----------------------------------------------------------------------------


@strawberry.enum
class GQLSignalType(Enum):
    ANALOG = "analog"
    DIGITAL = "digital"
    HYBRID = "hybrid"


@strawberry.enum
class GQLProcessorType(Enum):
    CLOUD = "cloud"
    LOCAL = "local"
    HYBRID = "hybrid"


@strawberry.enum
class GQLValidationStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


@strawberry.type
class GQLValidationResult:
    status: GQLValidationStatus
    is_valid: bool
    input_hash: str
    errors: List[str]
    warnings: List[str]


@strawberry.type
class GQLOutputSchema:
    result: str
    validation: GQLValidationResult
    processor_used: GQLProcessorType
    processing_time_ms: float
    retries_attempted: int


@strawberry.type
class Health:
    status: str = "ok"
    version: str = "0.1.0"


# -----------------------------------------------------------------------------
# Resolvers
# -----------------------------------------------------------------------------

processor_manager = ProcessorManager()


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> Health:
        return Health()


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def process_request(
        self,
        input_data: str,
        input_tokens: int,
        processor_type: GQLProcessorType = GQLProcessorType.HYBRID,
        timeout_seconds: float = 30.0,
    ) -> GQLOutputSchema:
        # Map GQL enum value to domain enum value
        request = ProcessingRequest(
            input_data=input_data,
            input_tokens=input_tokens,
            processor_type=ProcessorType(processor_type.value),
            timeout_seconds=timeout_seconds,
        )

        output = await processor_manager.process_request(request)

        return GQLOutputSchema(
            result=str(output.result),
            validation=GQLValidationResult(
                status=GQLValidationStatus(output.validation.status.value),
                is_valid=output.validation.is_valid,
                input_hash=output.validation.input_hash,
                errors=list(output.validation.errors),
                warnings=list(output.validation.warnings),
            ),
            processor_used=GQLProcessorType(output.processor_used.value),
            processing_time_ms=output.processing_time_ms,
            retries_attempted=output.retries_attempted,
        )


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def stream_processing(
        self,
        input_data: str,
        input_tokens: int,
        processor_type: GQLProcessorType = GQLProcessorType.HYBRID,
    ) -> AsyncGenerator[str, None]:
        request = ProcessingRequest(
            input_data=input_data,
            input_tokens=input_tokens,
            processor_type=ProcessorType(processor_type.value),
        )

        processor = processor_manager.get_processor(request)
        async for chunk in processor.stream_process(request):
            yield chunk


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
graphql_app = GraphQLRouter(schema)
