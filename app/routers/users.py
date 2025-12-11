from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.app_user import AppUser
from app.models.user_profile import UserProfile
from app.models.user_app_config import UserAppConfig
from app.models.user_trainer_config import UserTrainerConfig
from app.schemas.user import (
    AppUserResponse,
    AppUserCreate,
    AppUserUpdate,
    UserProfileResponse,
    UserProfileCreate,
    UserProfileUpdate,
    UserAppConfigResponse,
    UserAppConfigCreate,
    UserAppConfigUpdate,
    UserTrainerConfigResponse,
    UserTrainerConfigCreate,
    UserTrainerConfigUpdate,
)
from app.middleware.auth import get_current_user_id

router = APIRouter()


# ============================================================================
# APP USERS CRUD
# ============================================================================

@router.post("/users", response_model=AppUserResponse, status_code=status.HTTP_201_CREATED)
async def create_app_user(
    user: AppUserCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new app user"""
    # Verify the user is creating their own record
    try:
        user_uuid = UUID(current_user_id)
        if user.id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create your own user record"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check if user already exists
    existing_user = db.query(AppUser).filter(AppUser.id == user.id).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    db_user = AppUser(
        id=user.id,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        email=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users/me", response_model=AppUserResponse)
async def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get current user's information"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(AppUser).filter(AppUser.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/users/{user_id}", response_model=AppUserResponse)
async def get_app_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get a specific app user"""
    # Users can only view their own profile
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own profile"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user


@router.put("/users/{user_id}", response_model=AppUserResponse)
async def update_app_user(
    user_id: UUID,
    user: AppUserUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Update an app user"""
    # Users can only update their own profile
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Update fields
    update_data = user.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete an app user"""
    # Users can only delete their own profile
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own profile"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    db.delete(db_user)
    db.commit()
    return None


# ============================================================================
# USER PROFILE CRUD
# ============================================================================

@router.post("/users/{user_id}/profile", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    user_id: UUID,
    profile: UserProfileCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a user profile"""
    # Verify the user is creating their own profile
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid or profile.user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create your own profile"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check if profile already exists
    existing_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists"
        )
    
    db_profile = UserProfile(
        user_id=profile.user_id,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        birthday=profile.birthday,
        sex=profile.sex,
        fitness_level=profile.fitness_level,
        goal=profile.goal
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get a user profile"""
    # Users can only view their own profile
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own profile"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile for user {user_id} not found"
        )
    return profile


@router.put("/users/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: UUID,
    profile: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Update a user profile"""
    # Users can only update their own profile
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not db_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile for user {user_id} not found"
        )
    
    # Update fields
    update_data = profile.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile


@router.delete("/users/{user_id}/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a user profile"""
    # Users can only delete their own profile
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own profile"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not db_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile for user {user_id} not found"
        )
    
    db.delete(db_profile)
    db.commit()
    return None


# ============================================================================
# USER APP CONFIG CRUD
# ============================================================================

@router.post("/users/{user_id}/app-config", response_model=UserAppConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_user_app_config(
    user_id: UUID,
    config: UserAppConfigCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a user app config"""
    # Verify the user is creating their own config
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid or config.user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create your own config"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check if config already exists
    existing_config = db.query(UserAppConfig).filter(UserAppConfig.user_id == user_id).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="App config already exists"
        )
    
    db_config = UserAppConfig(
        user_id=config.user_id,
        preferences=config.preferences
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/users/{user_id}/app-config", response_model=UserAppConfigResponse)
async def get_user_app_config(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get a user app config"""
    # Users can only view their own config
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own config"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    config = db.query(UserAppConfig).filter(UserAppConfig.user_id == user_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App config for user {user_id} not found"
        )
    return config


@router.put("/users/{user_id}/app-config", response_model=UserAppConfigResponse)
async def update_user_app_config(
    user_id: UUID,
    config: UserAppConfigUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Update a user app config"""
    # Users can only update their own config
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own config"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_config = db.query(UserAppConfig).filter(UserAppConfig.user_id == user_id).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App config for user {user_id} not found"
        )
    
    # Update fields
    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/users/{user_id}/app-config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_app_config(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a user app config"""
    # Users can only delete their own config
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own config"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_config = db.query(UserAppConfig).filter(UserAppConfig.user_id == user_id).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App config for user {user_id} not found"
        )
    
    db.delete(db_config)
    db.commit()
    return None


# ============================================================================
# USER TRAINER CONFIG CRUD
# ============================================================================

@router.post("/users/{user_id}/trainer-config", response_model=UserTrainerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_user_trainer_config(
    user_id: UUID,
    config: UserTrainerConfigCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a user trainer config"""
    # Verify the user is creating their own config
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid or config.user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create your own config"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check if config already exists
    existing_config = db.query(UserTrainerConfig).filter(UserTrainerConfig.user_id == user_id).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trainer config already exists"
        )
    
    db_config = UserTrainerConfig(
        user_id=config.user_id,
        trainer_config=config.trainer_config
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/users/{user_id}/trainer-config", response_model=UserTrainerConfigResponse)
async def get_user_trainer_config(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get a user trainer config"""
    # Users can only view their own config
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own config"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    config = db.query(UserTrainerConfig).filter(UserTrainerConfig.user_id == user_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trainer config for user {user_id} not found"
        )
    return config


@router.put("/users/{user_id}/trainer-config", response_model=UserTrainerConfigResponse)
async def update_user_trainer_config(
    user_id: UUID,
    config: UserTrainerConfigUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Update a user trainer config"""
    # Users can only update their own config
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own config"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_config = db.query(UserTrainerConfig).filter(UserTrainerConfig.user_id == user_id).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trainer config for user {user_id} not found"
        )
    
    # Update fields
    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/users/{user_id}/trainer-config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_trainer_config(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a user trainer config"""
    # Users can only delete their own config
    try:
        current_uuid = UUID(current_user_id)
        if user_id != current_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own config"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_config = db.query(UserTrainerConfig).filter(UserTrainerConfig.user_id == user_id).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trainer config for user {user_id} not found"
        )
    
    db.delete(db_config)
    db.commit()
    return None

