from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# Workout Step Schemas
class WorkoutStepBase(BaseModel):
    """Base schema for WorkoutStep"""
    title: str
    description: Optional[str] = None
    estimated_duration_sec: Optional[int] = None
    category: Optional[str] = None
    media_url: Optional[str] = None
    instructions: Optional[str] = None
    exercise_type: Optional[str] = None
    default_reps: Optional[int] = None
    default_duration_sec: Optional[int] = None
    default_weight_kg: Optional[float] = None
    default_distance_m: Optional[float] = None


class WorkoutStepCreate(WorkoutStepBase):
    """Schema for creating a WorkoutStep"""
    pass


class WorkoutStepUpdate(BaseModel):
    """Schema for updating a WorkoutStep"""
    title: Optional[str] = None
    description: Optional[str] = None
    estimated_duration_sec: Optional[int] = None
    category: Optional[str] = None
    media_url: Optional[str] = None
    instructions: Optional[str] = None
    exercise_type: Optional[str] = None
    default_reps: Optional[int] = None
    default_duration_sec: Optional[int] = None
    default_weight_kg: Optional[float] = None
    default_distance_m: Optional[float] = None


class WorkoutStepResponse(WorkoutStepBase):
    """Schema for WorkoutStep response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Workout Package Schemas
class WorkoutPackageBase(BaseModel):
    """Base schema for WorkoutPackage"""
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    estimated_duration_sec: Optional[int] = None
    cover_image_url: Optional[str] = None
    steps: List[UUID] = []


class WorkoutPackageCreate(WorkoutPackageBase):
    """Schema for creating a WorkoutPackage"""
    user_id: Optional[UUID] = None


class WorkoutPackageUpdate(BaseModel):
    """Schema for updating a WorkoutPackage"""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    estimated_duration_sec: Optional[int] = None
    cover_image_url: Optional[str] = None
    steps: Optional[List[UUID]] = None


class WorkoutPackageResponse(WorkoutPackageBase):
    """Schema for WorkoutPackage response"""
    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkoutPackageFull(WorkoutPackageResponse):
    """Full WorkoutPackage with steps"""
    steps: List[WorkoutStepResponse] = []

    class Config:
        from_attributes = True

