import os
from typing import Optional
from app.services.llm_provider import LLMProviderInterface, GeminiProvider, OpenAIProvider
from pydantic_settings import BaseSettings


class LLMProviderSettings(BaseSettings):
    """Settings for LLM provider configuration"""
    llm_provider: str = "openai"  # Default provider
    gemini_api_key: Optional[str] = None
    gemini_model_name: str = "gemini-2.0-flash-exp"
    openai_api_key: Optional[str] = None
    openai_model_name: str = "gpt-4o-mini"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


def create_llm_provider(provider_name: Optional[str] = None) -> LLMProviderInterface:
    """
    Factory function to create LLM provider instances
    
    Args:
        provider_name: Name of provider to use (defaults to env config)
        
    Returns:
        LLMProviderInterface: Configured LLM provider instance
        
    Raises:
        ValueError: If provider is not supported or missing required config
    """
    settings = LLMProviderSettings()
    provider = provider_name or settings.llm_provider
    
    if provider == "gemini":
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        
        return GeminiProvider(
            api_key=api_key,
            model_name=settings.gemini_model_name
        )
    elif provider == "openai":
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        
        return OpenAIProvider(
            api_key=api_key,
            model_name=settings.openai_model_name
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
