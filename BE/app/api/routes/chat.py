from functools import lru_cache
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes.auth import optional_user
from app.api.routes.conversations import owned_conversation
from app.db.models import ChatMessage, Conversation, User
from app.db.session import get_db, utc_now
from app.services.chat import ChatService
from app.services.index import indexed_count


router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1000)
    session_id: str | None = Field(default=None, max_length=80)
    conversation_id: str | None = Field(default=None, max_length=36)


@lru_cache(maxsize=1)
def chat_service() -> ChatService:
    return ChatService()


@router.post("/chat")
def chat(request: ChatRequest, user: User | None = Depends(optional_user), db: Session = Depends(get_db)) -> dict:
    try:
        if indexed_count() == 0:
            raise HTTPException(status_code=503, detail="Chưa có chỉ mục RAG. Chạy: python -m app.scripts.ingest")
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=422, detail="Câu hỏi không được trống")
        if user is None:
            result = chat_service().ask(message, request.session_id)
            return {**result, "conversation_id": None}

        conversation = owned_conversation(db, user, request.conversation_id) if request.conversation_id else None
        conversation_id = conversation.id if conversation else str(uuid4())
        history_rows = []
        if conversation:
            history_rows = list(reversed(db.scalars(
                select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.desc()).limit(8)
            ).all()))
        history = [{"role": item.role, "text": item.content} for item in history_rows]
        result = chat_service().ask(message, conversation_id, history_override=history)
        if conversation is None:
            title = " ".join(message.split())[:80]
            conversation = Conversation(id=conversation_id, user_id=user.id, title=title)
            db.add(conversation)
            db.flush()
        db.add_all([
            ChatMessage(id=str(uuid4()), conversation_id=conversation_id, role="user", content=message, sources=[]),
            ChatMessage(id=str(uuid4()), conversation_id=conversation_id, role="assistant", content=result["answer"], sources=result["sources"]),
        ])
        conversation.updated_at = utc_now()
        db.commit()
        return {**result, "conversation_id": conversation_id}
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Không thể lưu hội thoại vào MySQL") from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Không thể truy vấn model local: {exc}") from exc
