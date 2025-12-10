from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class UserWorkoutSession(Base):
    """User workout session database model"""
    
    __tablename__ = "user_workout_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False)
    package_id = Column(UUID(as_uuid=True), ForeignKey("workout_packages.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_sec = Column(Integer, nullable=True)
    calories_estimated = Column(Integer, nullable=True)
    session_metadata = Column("metadata", JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("AppUser", back_populates="workout_sessions")
    package = relationship("WorkoutPackage", back_populates="sessions")
