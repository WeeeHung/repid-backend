from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserAppConfig(Base):
    """User app configuration database model"""
    
    __tablename__ = "user_app_config"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_users.id", ondelete="CASCADE"), primary_key=True)
    preferences = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("AppUser", back_populates="app_config")
