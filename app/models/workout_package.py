from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class WorkoutPackage(Base):
    """Workout package database model"""
    
    __tablename__ = "workout_packages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    estimated_duration_sec = Column(Integer, nullable=True)
    cover_image_url = Column(Text, nullable=True)
    voice_pack_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    steps = relationship("WorkoutStep", back_populates="package", cascade="all, delete-orphan", order_by="WorkoutStep.step_order")

