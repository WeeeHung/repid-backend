from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class AudioQueueItem(BaseModel):
    """Schema for a single audio queue item in the workout audio timeline.

    Each item corresponds to a logical voice event in the workout timeline.
    Special items:
    - order: 0 = start brief (only intro_audio_blob)
    - order: -1 = end debrief (only intro_audio_blob)
    """

    order: int = Field(..., description="Order of this item in the workout timeline (1-based, or 0 for brief, -1 for debrief)")
    intro_audio_blob: str = Field(..., description="Base64 encoded audio blob for the intro segment")
    start_audio_blob: str = Field(default="", description="Base64 encoded audio blob for the start segment (optional, empty for brief/debrief)")
    cue_audio_blobs: List[str] = Field(default_factory=list, description="List of base64 encoded audio blobs for cue segments (optional, empty for brief/debrief)")


class GenerateAudioRequest(BaseModel):
    """Request schema for generating workout audio"""
    workout_package_id: UUID


class GenerateAudioResponse(BaseModel):
    """Response schema for generated workout audio"""
    audio_queue: List[AudioQueueItem]

