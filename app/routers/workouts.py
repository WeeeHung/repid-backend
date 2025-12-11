from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.models.workout_package import WorkoutPackage
from app.models.workout_step import WorkoutStep
from app.schemas.workout import (
    WorkoutPackageResponse,
    WorkoutPackageCreate,
    WorkoutPackageUpdate,
    WorkoutPackageFull,
    WorkoutStepResponse,
    WorkoutStepCreate,
    WorkoutStepUpdate,
)
from app.middleware.auth import get_optional_user_id, get_current_user_id

router = APIRouter()


# ============================================================================
# WORKOUT PACKAGES CRUD
# ============================================================================

@router.post("/workouts", response_model=WorkoutPackageResponse, status_code=status.HTTP_201_CREATED)
async def create_workout_package(
    workout: WorkoutPackageCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new workout package"""
    # Convert user_id string to UUID if provided
    user_uuid = None
    if workout.user_id:
        user_uuid = workout.user_id
    elif user_id:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            pass
    
    db_workout = WorkoutPackage(
        title=workout.title,
        description=workout.description,
        category=workout.category,
        estimated_duration_sec=workout.estimated_duration_sec,
        cover_image_url=workout.cover_image_url,
        user_id=user_uuid,
        steps=workout.steps or []
    )
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout


@router.get("/workouts", response_model=List[WorkoutPackageResponse])
async def get_workouts(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Get workout packages with pagination and optional filters.
    
    By default, returns:
    - User's own packages (if authenticated)
    - Admin-created packages (where user_id is NULL)
    
    Use the user_id query parameter to filter by a specific user (admin use).
    """
    query = db.query(WorkoutPackage)
    
    # Apply category filter if provided
    if category:
        query = query.filter(WorkoutPackage.category == category)
    
    # If user_id query parameter is provided, filter by that specific user
    if user_id:
        try:
            user_uuid = UUID(user_id)
            query = query.filter(WorkoutPackage.user_id == user_uuid)
        except ValueError:
            pass
    else:
        # Default behavior: show user's packages + admin packages
        if current_user_id:
            # Authenticated user: show their packages + admin packages (user_id IS NULL)
            try:
                current_user_uuid = UUID(current_user_id)
                query = query.filter(
                    or_(
                        WorkoutPackage.user_id == current_user_uuid,
                        WorkoutPackage.user_id.is_(None)
                    )
                )
            except ValueError:
                # If UUID conversion fails, show only admin packages
                query = query.filter(WorkoutPackage.user_id.is_(None))
        else:
            # Unauthenticated: show only admin packages
            query = query.filter(WorkoutPackage.user_id.is_(None))
    
    workouts = query.offset(skip).limit(limit).all()
    return workouts


@router.get("/workouts/{package_id}", response_model=WorkoutPackageFull)
async def get_workout_package(
    package_id: UUID,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Get a full workout package with all steps
    
    Returns the complete workout package including:
    - Package metadata
    - All workout steps referenced in step_ids
    """
    # Get workout package
    workout = db.query(WorkoutPackage).filter(WorkoutPackage.id == package_id).first()
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout package with id {package_id} not found"
        )
    
    # Get all steps referenced in steps
    steps = []
    if workout.steps:
        # Extract IDs from steps list (assuming extraction logic remains similar)
        step_ids_list = workout.steps
        steps = (
            db.query(WorkoutStep)
            .filter(WorkoutStep.id.in_(step_ids_list))
            .all()
        )
        # Sort steps by the order in steps array
        step_dict = {str(step.id): step for step in steps}
        steps = [step_dict[str(step_id)] for step_id in step_ids_list if str(step_id) in step_dict]
    
    # Build full response
    response = {
        "id": workout.id,
        "title": workout.title,
        "description": workout.description,
        "category": workout.category,
        "estimated_duration_sec": workout.estimated_duration_sec,
        "cover_image_url": workout.cover_image_url,
        "user_id": workout.user_id,
        "created_at": workout.created_at,
        "updated_at": workout.updated_at,
        "steps": steps
    }
    
    return WorkoutPackageFull(**response)


@router.put("/workouts/{package_id}", response_model=WorkoutPackageResponse)
async def update_workout_package(
    package_id: UUID,
    workout: WorkoutPackageUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update a workout package"""
    db_workout = db.query(WorkoutPackage).filter(WorkoutPackage.id == package_id).first()
    if not db_workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout package with id {package_id} not found"
        )
    
    # Check if user owns this package or if it's public (user_id is None)
    try:
        user_uuid = UUID(user_id)
        if db_workout.user_id != user_uuid and db_workout.user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this workout package"
            )
    except ValueError:
        pass
    
    # Update fields
    update_data = workout.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_workout, field, value)
    
    db.commit()
    db.refresh(db_workout)
    return db_workout


@router.delete("/workouts/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout_package(
    package_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Delete a workout package"""
    db_workout = db.query(WorkoutPackage).filter(WorkoutPackage.id == package_id).first()
    if not db_workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout package with id {package_id} not found"
        )
    
    # Check if user owns this package or if it's public (user_id is None)
    try:
        user_uuid = UUID(user_id)
        if db_workout.user_id != user_uuid and db_workout.user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this workout package"
            )
    except ValueError:
        pass
    
    db.delete(db_workout)
    db.commit()
    return None


# ============================================================================
# WORKOUT STEPS CRUD
# ============================================================================

@router.post("/workout-steps", response_model=WorkoutStepResponse, status_code=status.HTTP_201_CREATED)
async def create_workout_step(
    step: WorkoutStepCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new workout step"""
    db_step = WorkoutStep(
        title=step.title,
        description=step.description,
        estimated_duration_sec=step.estimated_duration_sec,
        category=step.category,
        media_url=step.media_url,
        instructions=step.instructions,
        exercise_type=step.exercise_type,
        default_reps=step.default_reps,
        default_duration_sec=step.default_duration_sec,
        default_weight_kg=step.default_weight_kg,
        default_distance_m=step.default_distance_m
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


@router.get("/workout-steps", response_model=List[WorkoutStepResponse])
async def get_workout_steps(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """Get all workout steps with pagination"""
    steps = db.query(WorkoutStep).offset(skip).limit(limit).all()
    return steps


@router.get("/workout-steps/{step_id}", response_model=WorkoutStepResponse)
async def get_workout_step(
    step_id: UUID,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """Get a specific workout step"""
    step = db.query(WorkoutStep).filter(WorkoutStep.id == step_id).first()
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout step with id {step_id} not found"
        )
    return step


@router.put("/workout-steps/{step_id}", response_model=WorkoutStepResponse)
async def update_workout_step(
    step_id: UUID,
    step: WorkoutStepUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update a workout step"""
    db_step = db.query(WorkoutStep).filter(WorkoutStep.id == step_id).first()
    if not db_step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout step with id {step_id} not found"
        )
    
    # Update fields
    update_data = step.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_step, field, value)
    
    db.commit()
    db.refresh(db_step)
    return db_step


@router.delete("/workout-steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout_step(
    step_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Delete a workout step"""
    db_step = db.query(WorkoutStep).filter(WorkoutStep.id == step_id).first()
    if not db_step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout step with id {step_id} not found"
        )
    
    db.delete(db_step)
    db.commit()
    return None
