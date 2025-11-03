"""
System settings model for storing application configuration.
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from core.database import Base


class SystemSettings(Base):
    """
    System-wide settings stored in database.
    These override default values from config.py.
    """

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    timezone = Column(String(64), default="Europe/Madrid", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<SystemSettings(timezone={self.timezone})>"
