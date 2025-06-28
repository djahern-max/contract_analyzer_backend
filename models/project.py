# models/project.py - Add this relationship to your existing Project model
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Project(Base):
    __tablename__ = "projects"

    # Essential fields only
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Start with just these two core fields
    name = Column(String(255), nullable=False)
    description = Column(String(500))

    # Basic timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Essential relationships
    user = relationship("User", back_populates="projects")
    contracts = relationship("Contract", back_populates="project")  # ADD THIS LINE
