import logging
from ..services.llm_service import LLMService

logger = logging.getLogger(__name__)

class IntentService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def extract_entities(self, text):
        return self.llm_service.extract_entities(text)

    def generate_answer(self, text, context=None):
        return self.llm_service.generate_answer(text, context)
