from sqlalchemy import Column, String, Integer, Text, DateTime
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
    duration_sec = Column(Integer, nullable=True)
    posture_image_url = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

