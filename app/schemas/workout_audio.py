from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


class AudioQueueItem(BaseModel):
    """Schema for a single audio queue item"""
    step_id: str  # Changed to str to match the return value
    audio_blob: str = Field(..., description="Base64 encoded audio blob")
    transcript: str
    duration_sec: int = Field(None, description="Audio duration in seconds")


class GenerateAudioRequest(BaseModel):
    """Request schema for generating workout audio"""
    workout_package_id: UUID


class GenerateAudioResponse(BaseModel):
    """Response schema for generated workout audio"""
    audio_queue: List[AudioQueueItem]
