from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user_profile import UserProfile
from app.models.user_app_config import UserAppConfig
from app.models.user_trainer_config import UserTrainerConfig


class UserConfigService:
    """Service for loading and merging user configuration with defaults"""
    
    # Default trainer config values
    DEFAULT_TRAINER_CONFIG = {
        "voice_provider": "elevenlabs",
        "language": "en",
        "persona_style": "standard",
        "enthusiasm_cat": 3,
        "age_cat": 3,
        "gender": None,
        "speaking_rate": 1.0
    }
    
    # Default user preferences
    DEFAULT_PREFERENCES = {}
    
    @staticmethod
    def get_user_profile(db: Session, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user profile
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dict with profile data or None if not found
        """
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return None
        
        return {
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "birthday": profile.birthday,
            "sex": profile.sex,
            "fitness_level": profile.fitness_level,
            "goal": profile.goal
        }
    
    @staticmethod
    def get_user_preferences(db: Session, user_id: UUID) -> Dict[str, Any]:
        """
        Get user preferences merged with defaults
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dict with preferences (merged with defaults)
        """
        config = db.query(UserAppConfig).filter(UserAppConfig.user_id == user_id).first()
        user_prefs = config.preferences if config else {}
        
        # Merge with defaults (user preferences override defaults)
        merged = {**UserConfigService.DEFAULT_PREFERENCES, **user_prefs}
        return merged
    
    @staticmethod
    def get_trainer_config(db: Session, user_id: UUID, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get trainer config merged with defaults
        
        Args:
            db: Database session
            user_id: User ID
            user_profile: Optional user profile dict (to use sex as gender fallback)
            
        Returns:
            Dict with trainer config (merged with defaults)
        """
        config = db.query(UserTrainerConfig).filter(UserTrainerConfig.user_id == user_id).first()
        user_config = config.trainer_config if config else {}
        
        # Merge with defaults
        merged = {**UserConfigService.DEFAULT_TRAINER_CONFIG, **user_config}
        
        # If gender is not set, use from user_profile.sex
        if not merged.get("gender") and user_profile and user_profile.get("sex"):
            merged["gender"] = user_profile["sex"]
        
        return merged
    
    @staticmethod
    def get_all_user_config(db: Session, user_id: UUID) -> Dict[str, Any]:
        """
        Get all user configuration (profile, preferences, trainer_config)
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dict with profile, preferences, and trainer_config
        """
        profile = UserConfigService.get_user_profile(db, user_id)
        preferences = UserConfigService.get_user_preferences(db, user_id)
        trainer_config = UserConfigService.get_trainer_config(db, user_id, profile)
        
        return {
            "profile": profile,
            "preferences": preferences,
            "trainer_config": trainer_config
        }
