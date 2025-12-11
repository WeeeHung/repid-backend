from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.user_workout_session import UserWorkoutSession
from app.schemas.workout_session import (
    WorkoutSessionResponse,
    WorkoutSessionCreate,
    WorkoutSessionUpdate,
    SessionStartRequest,
    SessionStartResponse,
    SessionCompleteRequest,
    SessionCompleteResponse,
    SessionUpdateRequest,
)
from app.services.session_service import SessionService
from app.middleware.auth import get_current_user_id

router = APIRouter()


@router.post("/workout-sessions", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_workout_session(
    session: WorkoutSessionCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new workout session"""
    # Verify the user is creating their own session
    try:
        user_uuid = UUID(current_user_id)
        if session.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create your own workout sessions"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_session = UserWorkoutSession(
        user_id=session.user_id,
        package_id=session.package_id,
        started_at=session.started_at or datetime.utcnow(),
        ended_at=session.ended_at,
        session_metadata=session.metadata
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/workout-sessions", response_model=List[WorkoutSessionResponse])
async def get_workout_sessions(
    skip: int = 0,
    limit: int = 100,
    package_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get all workout sessions for the current user with pagination and optional filters"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    query = db.query(UserWorkoutSession).filter(UserWorkoutSession.user_id == user_uuid)
    
    if package_id:
        query = query.filter(UserWorkoutSession.package_id == package_id)
    
    sessions = query.order_by(UserWorkoutSession.started_at.desc()).offset(skip).limit(limit).all()
    return sessions


@router.get("/workout-sessions/{session_id}", response_model=WorkoutSessionResponse)
async def get_workout_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific workout session"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    session = db.query(UserWorkoutSession).filter(
        UserWorkoutSession.id == session_id,
        UserWorkoutSession.user_id == user_uuid
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout session with id {session_id} not found"
        )
    return session


@router.put("/workout-sessions/{session_id}", response_model=WorkoutSessionResponse)
async def update_workout_session(
    session_id: UUID,
    session: WorkoutSessionUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update a workout session"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_session = db.query(UserWorkoutSession).filter(
        UserWorkoutSession.id == session_id,
        UserWorkoutSession.user_id == user_uuid
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout session with id {session_id} not found"
        )
    
    # Update fields
    update_data = session.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_session, field, value)
    
    db.commit()
    db.refresh(db_session)
    return db_session


@router.delete("/workout-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Delete a workout session"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db_session = db.query(UserWorkoutSession).filter(
        UserWorkoutSession.id == session_id,
        UserWorkoutSession.user_id == user_uuid
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout session with id {session_id} not found"
        )
    
    db.delete(db_session)
    db.commit()
    return None


# ============================================================================
# SIMPLIFIED SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/workout/session/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_workout_session(
    request: SessionStartRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Start a new workout session (simplified endpoint)
    
    Creates a new workout session with started_at timestamp.
    Stores package_id and audio_queue_length in metadata.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    try:
        session_service = SessionService(db)
        session = session_service.start_session(
            user_id=user_uuid,
            package_id=request.workout_package_id,
            audio_queue_length=request.audio_queue_length
        )
        return SessionStartResponse(session_id=session.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting workout session: {str(e)}"
        )


@router.post("/workout/session/complete", response_model=SessionCompleteResponse)
async def complete_workout_session(
    request: SessionCompleteRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Complete a workout session (simplified endpoint)
    
    Updates session with ended_at, duration_sec, and completed_steps.
    Optionally stores user_metrics in metadata.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    try:
        session_service = SessionService(db)
        session = session_service.complete_session(
            session_id=request.session_id,
            user_id=user_uuid,
            total_duration_sec=request.total_duration_sec,
            completed_steps=request.completed_steps,
            user_metrics=request.user_metrics
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing workout session: {str(e)}"
        )


@router.post("/workout/session/update", response_model=WorkoutSessionResponse)
async def update_workout_session_progress(
    request: SessionUpdateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update workout session progress (optional endpoint)
    
    Updates session with current_step, progress_percent, and additional metadata.
    Useful for tracking progress during workout.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    try:
        session_service = SessionService(db)
        session = session_service.update_session(
            session_id=request.session_id,
            user_id=user_uuid,
            current_step=request.current_step,
            progress_percent=request.progress_percent,
            additional_metadata=request.additional_metadata
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating workout session: {str(e)}"
        )

