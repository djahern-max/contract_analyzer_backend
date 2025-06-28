# models/__init__.py
from .user import User
from .project import Project
from .contract import Contract

from .base import Base

# Export all models for easy importing
__all__ = ["Base", "User", "Project", "Contract"]
