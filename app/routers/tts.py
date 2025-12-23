from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.services.speech_factory import create_speech_provider
from app.services.storage import upload_audio_file
from app.middleware.auth import get_current_user_id

router = APIRouter()


class TTSGenerateRequest(BaseModel):
    """Request schema for TTS generation"""
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(None, description="Optional voice ID (defaults to provider default)")
    provider: str = Field("elevenlabs", description="TTS provider to use")


class TTSGenerateResponse(BaseModel):
    """Response schema for TTS generation"""
    audio_url: str
    transcript: str
    duration_sec: int = Field(None, description="Audio duration in seconds (if available)")


@router.post("/tts/generate", response_model=TTSGenerateResponse)
async def generate_tts(
    request: TTSGenerateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Generate TTS audio from text and upload to Supabase Storage
    
    This endpoint:
    1. Generates audio using the specified TTS provider
    2. Uploads the audio file to Supabase Storage
    3. Returns the public URL of the uploaded audio
    
    Used for package creation, not runtime playback.
    """
    try:
        # Create speech provider
        provider = create_speech_provider(provider_name=request.provider)
        
        # Generate audio
        audio_data = provider.generate_audio(
            text=request.text,
            voice_id=request.voice_id
        )
        
        # Upload to Supabase Storage
        audio_url = upload_audio_file(
            audio_data=audio_data,
            bucket_name="audio",
            content_type="audio/mpeg"
        )
        
        # Note: Duration calculation would require audio analysis
        # For MVP, we'll return None and let the client handle it
        # or use a library like mutagen to parse MP3 metadata
        
        return TTSGenerateResponse(
            audio_url=audio_url,
            transcript=request.text,
            duration_sec=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating TTS: {str(e)}"
        )


