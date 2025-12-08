from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.workout_package import WorkoutPackage
from app.models.workout_step import WorkoutStep
from app.models.voice_instruction import VoiceInstruction
from app.schemas.workout import (
    WorkoutPackageResponse,
    WorkoutPackageFull,
    WorkoutStepWithVoice,
)
from app.middleware.auth import get_optional_user_id

router = APIRouter()


@router.get("/workouts", response_model=List[WorkoutPackageResponse])
async def get_workouts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_optional_user_id)
):
    """Get all workout packages with pagination"""
    workouts = db.query(WorkoutPackage).offset(skip).limit(limit).all()
    return workouts


@router.get("/workouts/{package_id}", response_model=WorkoutPackageFull)
async def get_workout(
    package_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_optional_user_id)
):
    """
    Get a full workout package with all steps and voice instructions
    
    Returns the complete workout package including:
    - Package metadata
    - All workout steps in order
    - Voice instructions for each step
    """
    # Get workout package
    workout = db.query(WorkoutPackage).filter(WorkoutPackage.id == package_id).first()
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout package with id {package_id} not found"
        )
    
    # Get all steps ordered by step_order
    steps = (
        db.query(WorkoutStep)
        .filter(WorkoutStep.package_id == package_id)
        .order_by(WorkoutStep.step_order)
        .all()
    )
    
    # Build response with nested voice instructions
    steps_with_voice = []
    for step in steps:
        voice_instruction = None
        if step.voice_instruction_id:
            voice_instruction = (
                db.query(VoiceInstruction)
                .filter(VoiceInstruction.id == step.voice_instruction_id)
                .first()
            )
        
        step_dict = {
            "id": step.id,
            "package_id": step.package_id,
            "step_order": step.step_order,
            "title": step.title,
            "description": step.description,
            "duration_sec": step.duration_sec,
            "posture_image_url": step.posture_image_url,
            "voice_instruction_id": step.voice_instruction_id,
            "created_at": step.created_at,
            "updated_at": step.updated_at,
            "voice_instruction": voice_instruction
        }
        steps_with_voice.append(WorkoutStepWithVoice(**step_dict))
    
    # Build full response
    response = {
        "id": workout.id,
        "title": workout.title,
        "description": workout.description,
        "category": workout.category,
        "estimated_duration_sec": workout.estimated_duration_sec,
        "cover_image_url": workout.cover_image_url,
        "voice_pack_id": workout.voice_pack_id,
        "created_at": workout.created_at,
        "updated_at": workout.updated_at,
        "steps": steps_with_voice
    }
    
    return WorkoutPackageFull(**response)

