import os
from typing import Optional
from app.services.speech_provider import SpeechProviderInterface, ElevenLabsProvider
from pydantic_settings import BaseSettings


class SpeechProviderSettings(BaseSettings):
    """Settings for speech provider configuration"""
    tts_provider: str = "elevenlabs"  # Default provider
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_default_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


def create_speech_provider(provider_name: Optional[str] = None) -> SpeechProviderInterface:
    """
    Factory function to create speech provider instances
    
    Args:
        provider_name: Name of provider to use (defaults to env config)
        
    Returns:
        SpeechProviderInterface: Configured speech provider instance
        
    Raises:
        ValueError: If provider is not supported or missing required config
    """
    settings = SpeechProviderSettings()
    provider = provider_name or settings.tts_provider
    
    if provider == "elevenlabs":
        api_key = settings.elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is required for ElevenLabs provider")
        
        return ElevenLabsProvider(
            api_key=api_key,
            default_voice_id=settings.elevenlabs_default_voice_id
        )
    else:
        raise ValueError(f"Unsupported speech provider: {provider}")

