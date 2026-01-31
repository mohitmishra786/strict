from strict.core.math_engine import route_request
from strict.integrity.schemas import ProcessingRequest, OutputSchema
from strict.processors.openai_processor import OpenAIProcessor
from strict.processors.ollama_processor import OllamaProcessor
from strict.processors.groq_processor import GroqProcessor
from strict.core.interfaces import AsyncProcessor


class ProcessorManager:
    """Manages routing and execution of processors."""

    def __init__(self):
        self.openai_processor = OpenAIProcessor()
        self.ollama_processor = OllamaProcessor()
        self.groq_processor = GroqProcessor()

    def get_processor(self, request: ProcessingRequest) -> AsyncProcessor:
        """Determine which processor to use based on request."""
        decision = route_request(request)
        if decision == "cloud":
            # Routing logic: use Groq if requested in the data (mock logic)
            if "use_groq" in request.input_data.lower():
                return self.groq_processor
            return self.openai_processor
        return self.ollama_processor

    async def process_request(self, request: ProcessingRequest) -> OutputSchema:
        """Route and process the request."""
        processor = self.get_processor(request)
        return await processor.process(request)
