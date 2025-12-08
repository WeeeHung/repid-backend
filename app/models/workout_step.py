from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class WorkoutStep(Base):
    """Workout step database model"""
    
    __tablename__ = "workout_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("workout_packages.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    duration_sec = Column(Integer, nullable=False)
    posture_image_url = Column(Text, nullable=True)
    voice_instruction_id = Column(UUID(as_uuid=True), ForeignKey("voice_instructions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    package = relationship("WorkoutPackage", back_populates="steps")
    voice_instruction = relationship(
        "VoiceInstruction", 
        back_populates="step", 
        uselist=False,
        primaryjoin="WorkoutStep.id == VoiceInstruction.step_id"
    )
    
    __table_args__ = (
        UniqueConstraint('package_id', 'step_order', name='unique_package_step_order'),
    )

