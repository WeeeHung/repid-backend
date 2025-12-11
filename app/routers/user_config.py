from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.services.user_config_service import UserConfigService
from app.schemas.user import (
    UserProfileResponse,
    UserAppConfigResponse,
    UserTrainerConfigResponse
)
from app.middleware.auth import get_current_user_id

router = APIRouter()


@router.get("/user/profile", response_model=UserProfileResponse)
async def get_user_profile(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's profile (simplified endpoint)
    
    Auto-uses current user from authentication token.
    Returns 404 if profile doesn't exist.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    profile_data = UserConfigService.get_user_profile(db, user_uuid)
    if not profile_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Convert to response format
    from app.models.user_profile import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
    return profile


@router.get("/user/preferences", response_model=UserAppConfigResponse)
async def get_user_preferences(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's preferences merged with defaults (simplified endpoint)
    
    Auto-uses current user from authentication token.
    Returns preferences merged with default values.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    preferences = UserConfigService.get_user_preferences(db, user_uuid)
    
    # Return as UserAppConfigResponse format
    from app.models.user_app_config import UserAppConfig
    config = db.query(UserAppConfig).filter(UserAppConfig.user_id == user_uuid).first()
    
    if config:
        # Update with merged preferences
        config.preferences = preferences
        return config
    else:
        # Create response with defaults
        now = datetime.utcnow()
        return UserAppConfigResponse(
            user_id=user_uuid,
            preferences=preferences,
            created_at=now,
            updated_at=now
        )


@router.get("/user/trainer-config", response_model=UserTrainerConfigResponse)
async def get_user_trainer_config(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's trainer config merged with defaults (simplified endpoint)
    
    Auto-uses current user from authentication token.
    Returns trainer config merged with default values.
    Includes: voice_id, voice_provider, language, persona_style, age_cat, gender, enthusiasm_cat, speaking_rate
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Get user profile for gender fallback
    user_profile = UserConfigService.get_user_profile(db, user_uuid)
    trainer_config = UserConfigService.get_trainer_config(db, user_uuid, user_profile)
    
    # Return as UserTrainerConfigResponse format
    from app.models.user_trainer_config import UserTrainerConfig
    config = db.query(UserTrainerConfig).filter(UserTrainerConfig.user_id == user_uuid).first()
    
    if config:
        # Update with merged config
        config.trainer_config = trainer_config
        return config
    else:
        # Create response with defaults
        now = datetime.utcnow()
        return UserTrainerConfigResponse(
            user_id=user_uuid,
            trainer_config=trainer_config,
            created_at=now,
            updated_at=now
        )

