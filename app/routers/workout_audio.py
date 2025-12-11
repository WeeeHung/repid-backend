from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.services.workout_service import WorkoutService
from app.schemas.workout_audio import GenerateAudioRequest, GenerateAudioResponse
from app.middleware.auth import get_current_user_id

router = APIRouter()


@router.post("/workout/generate-audio", response_model=GenerateAudioResponse, status_code=status.HTTP_200_OK)
async def generate_workout_audio(
    request: GenerateAudioRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Generate personalized workout audio package
    
    This endpoint:
    1. Fetches user profile, preferences, and trainer_config
    2. Fetches workout package and steps
    3. Generates personalized scripts via LLM for each step
    4. Generates TTS audio for each script
    5. Returns audio queue with base64-encoded audio blobs and metadata
    
    Args:
        request: GenerateAudioRequest with workout_package_id
        db: Database session
        user_id: Current user ID from auth
        
    Returns:
        GenerateAudioResponse with audio_queue array containing audio_blob (base64), transcript, and duration_sec
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    try:
        workout_service = WorkoutService(db)
        audio_queue = workout_service.generate_audio_package(
            package_id=request.workout_package_id,
            user_id=user_uuid
        )
        
        return GenerateAudioResponse(audio_queue=audio_queue)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating workout audio: {str(e)}"
        )

