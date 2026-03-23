# filepath: market-research-platform/backend/api/routes/chat.py
# Chat API endpoints. Implements streaming Q&A over the document corpus.

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_llama_engine
from core.llamaindex_engine import LlamaIndexEngine
from core.query.chat_engine import ChatEngine
from models.chat_session import ChatSession

logger = logging.getLogger(__name__)

router = APIRouter()

# Cache of ChatEngine instances per session for multi-turn context
_chat_engines: dict[int, ChatEngine] = {}


@router.get("/stream")
async def stream_chat(
    q: str = Query(..., description="User's question"),
    session_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_session),
    engine: LlamaIndexEngine = Depends(get_llama_engine),
):
    """
    Server-Sent Events endpoint for streaming chat responses.
    Creates a new session if session_id is not provided.
    Streams tokens as 'token' events, then fires a final 'sources' event.
    """
    # Get or create chat session
    if session_id:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
    else:
        session = ChatSession(messages=[])
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # Get or create ChatEngine for this session
    chat_engine = _chat_engines.get(session.id)
    if not chat_engine:
        chat_engine = ChatEngine(engine)
        _chat_engines[session.id] = chat_engine

    # Get chat history for context
    chat_history = session.messages or []

    async def event_generator():
        full_response = ""
        sources = []

        try:
            async for chunk in chat_engine.stream_query(q, chat_history):
                if isinstance(chunk, dict):
                    # Final event with sources and full response
                    sources = chunk.get("sources", [])
                    full_response = chunk.get("full_response", full_response)
                else:
                    full_response += chunk
                    # Escape newlines for SSE data field
                    escaped = chunk.replace("\n", "\\n")
                    yield f"event: token\ndata: {escaped}\n\n"

            # Send sources event
            yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

            # Send session_id so the frontend knows which session to use
            yield f"event: session\ndata: {json.dumps({'session_id': session.id})}\n\n"

            # Persist the exchange to the session
            now = datetime.now(timezone.utc).isoformat()
            user_msg = {"role": "user", "content": q, "sources": [], "timestamp": now}
            assistant_msg = {
                "role": "assistant",
                "content": full_response,
                "sources": sources,
                "timestamp": now,
            }

            updated_messages = list(chat_history) + [user_msg, assistant_msg]

            # Update session in DB (using a fresh session to avoid conflicts)
            from database import AsyncSessionLocal
            async with AsyncSessionLocal() as update_db:
                result = await update_db.execute(
                    select(ChatSession).where(ChatSession.id == session.id)
                )
                db_session = result.scalar_one_or_none()
                if db_session:
                    db_session.messages = updated_messages
                    await update_db.commit()

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/sessions")
async def create_session(db: AsyncSession = Depends(get_session)):
    """Create a new chat session. Returns the session ID."""
    session = ChatSession(messages=[])
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {"session_id": session.id, "started_at": session.started_at.isoformat()}


@router.get("/sessions/{session_id}")
async def get_session_history(session_id: int, db: AsyncSession = Depends(get_session)):
    """Return the full message history for a given chat session."""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    return {
        "session_id": session.id,
        "started_at": session.started_at.isoformat(),
        "messages": session.messages or [],
    }


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: int, db: AsyncSession = Depends(get_session)):
    """Clear all messages from a chat session."""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    session.messages = []
    await db.commit()

    # Also clear the cached chat engine to reset context
    if session_id in _chat_engines:
        del _chat_engines[session_id]

    return {"cleared": True, "session_id": session_id}
