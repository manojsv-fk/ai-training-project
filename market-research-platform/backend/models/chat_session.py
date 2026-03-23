# filepath: market-research-platform/backend/models/chat_session.py
# ORM model for chat sessions. Each session holds an ordered list of
# messages (user + assistant) with source citations.
# Session history is preserved within a browser session.

from datetime import datetime
from sqlalchemy import DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    messages: Mapped[list] = mapped_column(
        JSON, default=list
    )
    # Message format:
    # {
    #   "role": "user" | "assistant",
    #   "content": "...",
    #   "sources": [{"source_name": "...", "page": 3, "document_id": 7}],
    #   "timestamp": "2024-01-01T10:00:00Z"
    # }

    # TODO: Add ended_at field (set when session is explicitly cleared)
    # TODO: Add user identifier field (post-POC, once auth is added)

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} messages={len(self.messages or [])}>"
