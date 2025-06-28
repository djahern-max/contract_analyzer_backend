# models/contract.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Basic file info
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)

    # All flexible contract data stored as JSON
    contract_data = Column(JSONB, default={})

    # Processing status
    is_processed = Column(
        String(50), default="pending"
    )  # pending, processing, completed, failed
    processed_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    project = relationship("Project", back_populates="contracts")
