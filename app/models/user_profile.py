from sqlalchemy import Column, Integer, Date, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserProfile(Base):
    """User profile database model"""
    
    __tablename__ = "user_profile"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_users.id", ondelete="CASCADE"), primary_key=True)
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)
    birthday = Column(Date, nullable=True)
    sex = Column(Text, nullable=True)
    fitness_level = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("AppUser", back_populates="profile")
    
    __table_args__ = (
        CheckConstraint("sex IN ('male', 'female', 'other')", name='check_sex'),
        CheckConstraint("fitness_level IN ('beginner', 'intermediate', 'advanced')", name='check_fitness_level'),
        CheckConstraint("goal IN ('lose_fat', 'build_muscle', 'general_fitness')", name='check_goal'),
    )

