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

    # Get all steps referenced in timeline
    timeline = []
    if workout.timeline:
        # workout.timeline can be a list of IDs (strings/UUIDs) or a list of dicts (overrides)
        step_ids_list = []
        step_overrides = {}
        for item in workout.timeline:
            if isinstance(item, dict):
                # Handle dict with overrides
                # The ID might be stored as "id" or "step_id" depending on how it was saved
                s_id = item.get("id") or item.get("step_id")
                if s_id:
                    step_ids_list.append(s_id)
                    step_overrides[str(s_id)] = item
            else:
                # Handle plain ID (string or UUID)
                step_ids_list.append(item)
        
        # Fetch steps from DB
        db_steps = (
            db.query(WorkoutStep)
            .filter(WorkoutStep.id.in_(step_ids_list))
            .all()
        )
        
        # Create map for quick lookup
        step_db_map = {str(step.id): step for step in db_steps}
        
        # Build final list preserving order
        for item in workout.timeline:
            # Determine ID again
            s_id = None
            override_data = {}
            
            if isinstance(item, dict):
                s_id = item.get("id") or item.get("step_id")
                override_data = item
            else:
                s_id = item
            
            s_id_str = str(s_id)
            if s_id_str in step_db_map:
                db_step = step_db_map[s_id_str]
                
                # Base step data (convert SQLAlchemy model to dict)
                step_data = {
                    "step_id": db_step.id,
                    "title": db_step.title,
                    "description": db_step.description,
                    "category": db_step.category,
                    "estimated_duration_sec": db_step.estimated_duration_sec,
                    "media_url": db_step.media_url,
                    "instructions": db_step.instructions,
                    "exercise_type": db_step.exercise_type,
                    "default_reps": db_step.default_reps,
                    "default_duration_sec": db_step.default_duration_sec,
                    "default_weight_kg": db_step.default_weight_kg,
                    "default_distance_m": db_step.default_distance_m,
                    # Backward compatibility for 'id' field
                    "id": db_step.id, 
                }
                
                # Apply merging logic
                if "sets" in override_data:
                    # Case 1: Explicit sets in override
                    step_data["sets"] = override_data["sets"]
                    if "rest_between_sets_s" in override_data:
                        step_data["rest_between_sets_s"] = override_data["rest_between_sets_s"]
                elif override_data:
                    # Case 1b: Override exists but no sets (maybe just specific reps override?)
                    # If the override has specific fields like 'reps', use them.
                    # Otherwise fall back to defaults mapping.
                    if "reps" in override_data:
                         step_data["reps"] = override_data["reps"]
                    else:
                         step_data["reps"] = db_step.default_reps
                         
                    if "weight_kg" in override_data:
                         step_data["weight_kg"] = override_data["weight_kg"]
                    else:
                         step_data["weight_kg"] = db_step.default_weight_kg
                         
                    # Check for other overrides if present in input
                    if "distance_m" in override_data:
                        step_data["distance_m"] = override_data["distance_m"]
                    elif db_step.default_distance_m:
                        step_data["distance_m"] = db_step.default_distance_m
                else:
                    # Case 2: No override (just ID), fallback to defaults flat mapping
                    # Map default_* to flat fields
                    step_data["reps"] = db_step.default_reps
                    step_data["weight_kg"] = db_step.default_weight_kg
                    step_data["duration_sec"] = db_step.default_duration_sec
                    step_data["distance_m"] = db_step.default_distance_m
                
                timeline.append(step_data)
    
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
        "timeline": timeline
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
