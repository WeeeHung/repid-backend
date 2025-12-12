from abc import ABC, abstractmethod
from typing import Optional
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs


class SpeechProviderInterface(ABC):
    """Abstract interface for speech providers"""
    
    @abstractmethod
    def generate_audio(self, text: str, voice_id: Optional[str] = None, **kwargs) -> bytes:
        """
        Generate audio from text using TTS
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID to use
            **kwargs: Additional provider-specific parameters
            
        Returns:
            bytes: Audio data (typically MP3 or WAV)
        """
        raise NotImplementedError


class ElevenLabsProvider(SpeechProviderInterface):
    """ElevenLabs TTS provider implementation"""
    
    def __init__(self, api_key: str, default_voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        """
        Initialize ElevenLabs provider
        
        Args:
            api_key: ElevenLabs API key
            default_voice_id: Default voice ID to use (Rachel by default)
        """
        self.api_key = api_key
        self.default_voice_id = default_voice_id
        self.client = ElevenLabs(api_key=api_key)
    
    def generate_audio(self, text: str, voice_id: Optional[str] = None, **kwargs) -> bytes:
        """
        Generate audio using ElevenLabs TTS
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (defaults to instance default)
            **kwargs: Additional parameters:
                - model_id: TTS model to use
                - voice_settings: VoiceSettings object for customization
                
        Returns:
            bytes: Audio data (MP3 format)
        """
        voice = voice_id or self.default_voice_id
        model_id = kwargs.get("model_id", "eleven_turbo_v2_5")
        voice_settings = kwargs.get("voice_settings", VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True
        ))
        
        # The convert method returns an iterator of bytes, so we need to collect them
        audio_chunks = self.client.text_to_speech.convert(
            voice_id=voice,
            text=text,
            model_id=model_id,
            voice_settings=voice_settings,
            output_format="mp3_22050_32"  # MP3 format
        )
        
        # Collect all audio chunks into a single bytes object
        audio = b"".join(audio_chunks)
        
        return audio

