# filepath: market-research-platform/backend/models/__init__.py
# Exports all ORM models so they are registered with SQLAlchemy's metadata
# before init_db() calls Base.metadata.create_all().

from .document import Document
from .report import Report
from .chat_session import ChatSession
from .trend import Trend

__all__ = ["Document", "Report", "ChatSession", "Trend"]
