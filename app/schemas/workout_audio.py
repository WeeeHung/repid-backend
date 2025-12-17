from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


class AudioQueueItem(BaseModel):
    """Schema for a single audio queue item in the workout audio timeline.

    Each item corresponds to a logical voice event in the workout timeline.
    """

    order: int = Field(..., description="Order of this item in the workout timeline (1-based)")
    intro_audio_blob: str = Field(..., description="Base64 encoded audio blob for the intro segment")
    start_audio_blob: str = Field(..., description="Base64 encoded audio blob for the start segment")
    cue_audio_blobs: List[str] = Field(..., description="List of base64 encoded audio blobs for cue segments.")


class GenerateAudioRequest(BaseModel):
    """Request schema for generating workout audio"""
    workout_package_id: UUID


class GenerateAudioResponse(BaseModel):
    """Response schema for generated workout audio"""
    audio_queue: List[AudioQueueItem]

