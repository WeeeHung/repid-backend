from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AppUser(Base):
    """App user database model"""
    
    __tablename__ = "app_users"
    
    # Note: Foreign key to auth.users.id is enforced at the database level
    # We don't define it here to avoid SQLAlchemy validation issues with cross-schema references
    id = Column(UUID(as_uuid=True), primary_key=True)
    full_name = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    app_config = relationship("UserAppConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trainer_config = relationship("UserTrainerConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    workout_packages = relationship("WorkoutPackage", back_populates="user")
    workout_sessions = relationship("UserWorkoutSession", back_populates="user")
