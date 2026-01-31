from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from app.llm.schemas import LLMResponse

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, timeout: int =30) -> LLMResponse:
        pass
    @abstractmethod
    def is_available(self)->bool:
        pass

class LLMError(Exception):
    
    def __init__(self, message: str, original_error: Optional[Exception]= None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)
        
def get_llm_client() -> Optional[LLMClient]:
    from app.core.config import settings
    from app.llm.openrouter_client import OpenRouterClient
    
    if hasattr(settings, 'OPENROUTER_API_KEY') and settings.OPENROUTER_API_KEY:
        api_key = settings.OPENROUTER_API_KEY
        
        # Check if it's a real API key (not empty or placeholder)
        if api_key and not api_key.startswith("your-") and api_key != "":
            logger.info("LLM client initialized with OpenRouter")
            return OpenRouterClient()
    
    logger.info("LLM client not configured - running in rule-only mode")
    return None
