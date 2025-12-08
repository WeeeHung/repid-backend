from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# Voice Instruction Schemas
class VoiceInstructionBase(BaseModel):
    """Base schema for VoiceInstruction"""
    tts_provider: str
    audio_url: str
    transcript: str
    duration_sec: Optional[int] = None


class VoiceInstructionCreate(VoiceInstructionBase):
    """Schema for creating a VoiceInstruction"""
    step_id: UUID


class VoiceInstructionResponse(VoiceInstructionBase):
    """Schema for VoiceInstruction response"""
    id: UUID
    step_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Workout Step Schemas
class WorkoutStepBase(BaseModel):
    """Base schema for WorkoutStep"""
    step_order: int = Field(..., gt=0)
    title: str
    description: Optional[str] = None
    duration_sec: int = Field(..., gt=0)
    posture_image_url: Optional[str] = None


class WorkoutStepCreate(WorkoutStepBase):
    """Schema for creating a WorkoutStep"""
    package_id: UUID
    voice_instruction_id: Optional[UUID] = None


class WorkoutStepResponse(WorkoutStepBase):
    """Schema for WorkoutStep response"""
    id: UUID
    package_id: UUID
    voice_instruction_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkoutStepWithVoice(WorkoutStepResponse):
    """WorkoutStep with nested voice instruction"""
    voice_instruction: Optional[VoiceInstructionResponse] = None

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
    voice_pack_id: Optional[UUID] = None


class WorkoutPackageCreate(WorkoutPackageBase):
    """Schema for creating a WorkoutPackage"""
    pass


class WorkoutPackageResponse(WorkoutPackageBase):
    """Schema for WorkoutPackage response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkoutPackageWithSteps(WorkoutPackageResponse):
    """WorkoutPackage with nested steps"""
    steps: List[WorkoutStepResponse] = []

    class Config:
        from_attributes = True


class WorkoutPackageFull(WorkoutPackageResponse):
    """Full WorkoutPackage with steps and voice instructions"""
    steps: List[WorkoutStepWithVoice] = []

    class Config:
        from_attributes = True

