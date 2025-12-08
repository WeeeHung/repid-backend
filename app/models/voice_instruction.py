from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class VoiceInstruction(Base):
    """Voice instruction database model"""
    
    __tablename__ = "voice_instructions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_id = Column(UUID(as_uuid=True), ForeignKey("workout_steps.id", ondelete="CASCADE"), nullable=False)
    tts_provider = Column(Text, nullable=False)
    audio_url = Column(Text, nullable=False)
    transcript = Column(Text, nullable=False)
    duration_sec = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    step = relationship("WorkoutStep", back_populates="voice_instruction", foreign_keys=[step_id])

