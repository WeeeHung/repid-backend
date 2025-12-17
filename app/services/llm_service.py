import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from google import genai


class LLMSettings(BaseSettings):
    """Settings for LLM service configuration"""
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

class LLMService:
    """Service for generating personalized workout scripts using Gemini"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM service
        
        Args:
            api_key: Gemini API key (defaults to env variable)
        """
        settings = LLMSettings()
        self.api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for LLM service")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = 'gemini-1.5-flash'