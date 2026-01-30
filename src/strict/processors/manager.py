from strict.core.math_engine import route_request
from strict.integrity.schemas import ProcessingRequest, OutputSchema
from strict.processors.openai_processor import OpenAIProcessor
from strict.processors.ollama_processor import OllamaProcessor


class ProcessorManager:
    """Manages routing and execution of processors."""

    def __init__(self):
        self.cloud_processor = OpenAIProcessor()
        self.local_processor = OllamaProcessor()

    async def process_request(self, request: ProcessingRequest) -> OutputSchema:
        """Route and process the request."""
        # Pure logic decision
        decision = route_request(request)

        if decision == "cloud":
            return await self.cloud_processor.process(request)
        else:
            return await self.local_processor.process(request)
