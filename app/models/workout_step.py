from sqlalchemy import Column, String, Integer, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class WorkoutStep(Base):
    """Workout step database model"""
    
    __tablename__ = "workout_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    estimated_duration_sec = Column(Integer, nullable=True)
    category = Column(Text, nullable=True)
    media_url = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    exercise_type = Column(Text, nullable=True)
    
    # Optional defaults
    default_reps = Column(Integer, nullable=True)
    default_duration_sec = Column(Integer, nullable=True)
    default_weight_kg = Column(Float, nullable=True)
    default_distance_m = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

