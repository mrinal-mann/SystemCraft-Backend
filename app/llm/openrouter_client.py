import json
import logging
import time
from typing import Optional

import httpx  # async HTTP client (install: pip install httpx)

from app.core.config import settings
from app.llm.client import LLMClient, LLMError
from app.llm.schemas import LLMResponse
from app.llm.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OpenRouterClient(LLMClient):
    """
    OpenRouter API client.
    
    Configuration (via environment variables):
        OPENROUTER_API_KEY: Your API key from openrouter.ai
        OPENROUTER_MODEL: Model to use (default: openai/gpt-3.5-turbo)
    
    API Endpoint: https://openrouter.ai/api/v1/chat/completions
    """
    
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self):
        """Initialize the OpenRouter client."""
        self.api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        self.model = getattr(settings, 'OPENROUTER_MODEL', 'openai/gpt-3.5-turbo')
        self.app_name = getattr(settings, 'PROJECT_NAME', 'System Design Mentor')
    
    def is_available(self) -> bool:
        """Check if OpenRouter is configured."""
        return bool(self.api_key and not self.api_key.startswith("your-"))
    
    async def generate(self, prompt: str, timeout: int = 30) -> LLMResponse:
        """
        Generate a response from OpenRouter.
        
        Args:
            prompt: The user prompt (system prompt is added automatically)
            timeout: Request timeout in seconds
        
        Returns:
            LLMResponse: Validated response
        
        Raises:
            LLMError: If API call fails or response is invalid
        """
        if not self.is_available():
            raise LLMError("OpenRouter API key not configured")
        
        start_time = time.time()
        
        # Build request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://system-design-mentor.local",  # Optional: your app URL
            "X-Title": self.app_name,  # Optional: your app name
        }
        
        # Build request body (OpenAI-compatible format)
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            # Request JSON output
            "response_format": {"type": "json_object"},
            # Reasonable defaults
            "temperature": 0.3,  # Lower = more deterministic
            "max_tokens": 2000,  # Enough for explanations
        }
        
        try:
            # Make async HTTP request
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=request_body,
                )
            
            # Log latency
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"OpenRouter response in {latency_ms}ms, status={response.status_code}")
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                raise LLMError(f"OpenRouter API returned {response.status_code}: {error_detail}")
            
            # Parse response
            response_json = response.json()
            
            # Extract message content
            # OpenRouter response format: {"choices": [{"message": {"content": "..."}}]}
            choices = response_json.get("choices", [])
            if not choices:
                raise LLMError("OpenRouter returned empty choices")
            
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise LLMError("OpenRouter returned empty content")
            
            # Log the raw response for debugging
            logger.debug(f"LLM raw response: {content[:500]}...")
            
            # Parse and validate JSON
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"LLM returned invalid JSON: {content[:200]}")
                raise LLMError(f"Invalid JSON from LLM: {e}")
            
            # Validate against schema
            try:
                llm_response = LLMResponse(**parsed)
            except Exception as e:
                logger.error(f"LLM response failed schema validation: {e}")
                raise LLMError(f"Schema validation failed: {e}")
            
            return llm_response
            
        except httpx.TimeoutException:
            logger.error(f"OpenRouter request timed out after {timeout}s")
            raise LLMError(f"Request timed out after {timeout} seconds")
        
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            raise LLMError(f"HTTP request failed: {e}")