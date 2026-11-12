from functools import lru_cache
from hashlib import sha256
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes.auth import optional_user
from app.api.routes.conversations import owned_conversation
from app.core.config import settings
from app.db.models import ChatMessage, ChatRequestRecord, Conversation, User
from app.db.session import get_db, utc_now
from app.services.chat import ChatService
from app.services.index import indexed_count


router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1000)
    session_id: str | None = Field(default=None, max_length=80)
    conversation_id: str | None = Field(default=None, max_length=36)
    request_id: UUID | None = None


def _request_hash(message: str, conversation_id: str | None) -> str:
    return sha256((message + "\0" + (conversation_id or "")).encode("utf-8")).hexdigest()


def _replayed(db: Session, user: User, request_id: str, fingerprint: str) -> dict | None:
    record = db.scalar(select(ChatRequestRecord).where(
        ChatRequestRecord.user_id == user.id, ChatRequestRecord.request_id == request_id
    ))
    if record is None:
        return None
    if record.message_hash != fingerprint:
        raise HTTPException(status_code=409, detail="request_id đã được dùng cho yêu cầu khác")
    return record.response_json


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

        request_id = str(request.request_id) if request.request_id else None
        fingerprint = _request_hash(message, request.conversation_id)
        if request_id:
            replay = _replayed(db, user, request_id, fingerprint)
            if replay is not None:
                return replay
        conversation = owned_conversation(db, user, request.conversation_id) if request.conversation_id else None
        conversation_id = conversation.id if conversation else str(uuid4())
        history_rows = []
        if conversation:
            history_rows = list(reversed(db.scalars(
                select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.desc()).limit(settings.chat_context_turns * 2)
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
        response = {**result, "conversation_id": conversation_id}
        if request_id:
            db.add(ChatRequestRecord(user_id=user.id, request_id=request_id, message_hash=fingerprint,
                                     conversation_id=conversation_id, response_json=response))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if request_id:
                replay = _replayed(db, user, request_id, fingerprint)
                if replay is not None:
                    return replay
            raise
        return response
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Không thể lưu hội thoại vào MySQL") from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Không thể truy vấn model local: {exc}") from exc
