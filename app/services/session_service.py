from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.models.user_workout_session import UserWorkoutSession


class SessionService:
    """Service for workout session management"""
    
    def __init__(self, db: Session):
        """
        Initialize session service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def start_session(
        self,
        user_id: UUID,
        package_id: UUID,
        audio_queue_length: int
    ) -> UserWorkoutSession:
        """
        Start a new workout session
        
        Args:
            user_id: User ID
            package_id: Workout package ID
            audio_queue_length: Number of audio items in queue
            
        Returns:
            UserWorkoutSession model
        """
        session = UserWorkoutSession(
            user_id=user_id,
            package_id=package_id,
            started_at=datetime.utcnow(),
            session_metadata={
                "audio_queue_length": audio_queue_length,
                "completed_steps": []
            }
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def complete_session(
        self,
        session_id: UUID,
        user_id: UUID,
        total_duration_sec: int,
        completed_steps: List[str],
        user_metrics: Optional[Dict[str, Any]] = None
    ) -> UserWorkoutSession:
        """
        Complete a workout session
        
        Args:
            session_id: Session ID
            user_id: User ID (for validation)
            total_duration_sec: Total duration in seconds
            completed_steps: List of completed step IDs
            user_metrics: Optional user metrics dict
            
        Returns:
            Updated UserWorkoutSession model
            
        Raises:
            ValueError: If session not found or doesn't belong to user
        """
        session = self.db.query(UserWorkoutSession).filter(
            UserWorkoutSession.id == session_id,
            UserWorkoutSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found or doesn't belong to user")
        
        # Update session
        session.ended_at = datetime.utcnow()
        session.duration_sec = total_duration_sec
        
        # Update metadata
        metadata = session.session_metadata or {}
        metadata["completed_steps"] = completed_steps
        if user_metrics:
            metadata["user_metrics"] = user_metrics
        session.session_metadata = metadata
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def update_session(
        self,
        session_id: UUID,
        user_id: UUID,
        current_step: Optional[int] = None,
        progress_percent: Optional[float] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> UserWorkoutSession:
        """
        Update session progress (optional)
        
        Args:
            session_id: Session ID
            user_id: User ID (for validation)
            current_step: Current step index
            progress_percent: Progress percentage (0-100)
            additional_metadata: Additional metadata to merge
            
        Returns:
            Updated UserWorkoutSession model
            
        Raises:
            ValueError: If session not found or doesn't belong to user
        """
        session = self.db.query(UserWorkoutSession).filter(
            UserWorkoutSession.id == session_id,
            UserWorkoutSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found or doesn't belong to user")
        
        # Update metadata
        metadata = session.session_metadata or {}
        if current_step is not None:
            metadata["current_step"] = current_step
        if progress_percent is not None:
            metadata["progress_percent"] = progress_percent
        if additional_metadata:
            metadata.update(additional_metadata)
        session.session_metadata = metadata
        
        self.db.commit()
        self.db.refresh(session)
        return session

