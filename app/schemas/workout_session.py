from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class WorkoutSessionBase(BaseModel):
    """Base schema for UserWorkoutSession"""
    package_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkoutSessionCreate(WorkoutSessionBase):
    """Schema for creating a UserWorkoutSession"""
    user_id: UUID


class WorkoutSessionUpdate(BaseModel):
    """Schema for updating a UserWorkoutSession"""
    package_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkoutSessionResponse(WorkoutSessionBase):
    """Schema for UserWorkoutSession response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}
    
    @model_validator(mode='before')
    @classmethod
    def map_session_metadata(cls, data):
        """Map session_metadata from model to metadata in schema"""
        if isinstance(data, dict):
            if 'session_metadata' in data and 'metadata' not in data:
                data['metadata'] = data.pop('session_metadata')
        elif hasattr(data, 'session_metadata'):
            # Convert object to dict for processing
            return {
                'id': data.id,
                'user_id': data.user_id,
                'package_id': data.package_id,
                'started_at': data.started_at,
                'ended_at': data.ended_at,
                'metadata': data.session_metadata,
                'created_at': data.created_at,
                'updated_at': data.updated_at,
            }
        return data


# Session management schemas
class SessionStartRequest(BaseModel):
    """Request schema for starting a workout session"""
    workout_package_id: UUID
    workout_title: str = Field(..., description="Title of the workout")
    exercises: List[str] = Field(default_factory=list, description="List of exercise names in the workout")


class SessionStartResponse(BaseModel):
    """Response schema for starting a workout session"""
    session_id: UUID


class SessionCompleteRequest(BaseModel):
    """Request schema for completing a workout session"""
    session_id: UUID
    effort: Optional[int] = Field(None, ge=1, le=5, description="Perceived exertion (1-5)")
    mood: Optional[int] = Field(None, ge=1, le=5, description="Post-workout mood (1-5)")


class SessionCompleteResponse(WorkoutSessionResponse):
    """Response schema for completing a workout session"""
    pass


class SessionUpdateRequest(BaseModel):
    """Request schema for updating a workout session"""
    session_id: UUID
    current_step: Optional[int] = Field(None, ge=0, description="Current step index")
    progress_percent: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata to merge")

