from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date


# App User Schemas
class AppUserBase(BaseModel):
    """Base schema for AppUser"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None


class AppUserCreate(AppUserBase):
    """Schema for creating an AppUser"""
    id: UUID


class AppUserUpdate(BaseModel):
    """Schema for updating an AppUser"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None


class AppUserResponse(AppUserBase):
    """Schema for AppUser response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Profile Schemas
class UserProfileBase(BaseModel):
    """Base schema for UserProfile"""
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    birthday: Optional[date] = None
    sex: Optional[str] = Field(None, pattern="^(male|female|other)$")
    fitness_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    goal: Optional[str] = Field(None, pattern="^(lose_fat|build_muscle|general_fitness)$")


class UserProfileCreate(UserProfileBase):
    """Schema for creating a UserProfile"""
    user_id: UUID


class UserProfileUpdate(BaseModel):
    """Schema for updating a UserProfile"""
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    birthday: Optional[date] = None
    sex: Optional[str] = Field(None, pattern="^(male|female|other)$")
    fitness_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    goal: Optional[str] = Field(None, pattern="^(lose_fat|build_muscle|general_fitness)$")


class UserProfileResponse(UserProfileBase):
    """Schema for UserProfile response"""
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User App Config Schemas
class UserAppConfigBase(BaseModel):
    """Base schema for UserAppConfig"""
    preferences: Dict[str, Any] = {}


class UserAppConfigCreate(UserAppConfigBase):
    """Schema for creating a UserAppConfig"""
    user_id: UUID


class UserAppConfigUpdate(BaseModel):
    """Schema for updating a UserAppConfig"""
    preferences: Optional[Dict[str, Any]] = None


class UserAppConfigResponse(UserAppConfigBase):
    """Schema for UserAppConfig response"""
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Trainer Config Schemas
class UserTrainerConfigBase(BaseModel):
    """Base schema for UserTrainerConfig"""
    trainer_config: Dict[str, Any] = {}


class UserTrainerConfigCreate(UserTrainerConfigBase):
    """Schema for creating a UserTrainerConfig"""
    user_id: UUID


class UserTrainerConfigUpdate(BaseModel):
    """Schema for updating a UserTrainerConfig"""
    trainer_config: Optional[Dict[str, Any]] = None


class UserTrainerConfigResponse(UserTrainerConfigBase):
    """Schema for UserTrainerConfig response"""
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

