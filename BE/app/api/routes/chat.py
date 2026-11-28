from datetime import timedelta
from functools import lru_cache
from hashlib import sha256
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes.auth import optional_user
from app.api.routes.conversations import owned_conversation
from app.core.config import settings
from app.core.rate_limit import CHAT_LIMIT, client_key, limiter
from app.db.models import ChatMessage, ChatRequestRecord, Conversation, User, message_order
from app.db.session import get_db, utc_now
from app.services.chat import ChatService
from app.services.index import indexed_count


logger = logging.getLogger(__name__)
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
def chat(request: ChatRequest, http_request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)) -> dict:
    limiter.check(client_key(http_request, "chat"), CHAT_LIMIT)
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
                .order_by(*message_order(descending=True)).limit(settings.chat_context_turns * 2)
            ).all()))
        history = [{"role": item.role, "text": item.content} for item in history_rows]
        result = chat_service().ask(message, conversation_id, history_override=history)
        if conversation is None:
            title = " ".join(message.split())[:80]
            conversation = Conversation(id=conversation_id, user_id=user.id, title=title)
            db.add(conversation)
            db.flush()
        # Gán thời điểm tường minh: câu trả lời luôn sau câu hỏi ít nhất 1 micro giây.
        asked_at = utc_now()
        answered_at = asked_at + timedelta(microseconds=1)
        db.add_all([
            ChatMessage(id=str(uuid4()), conversation_id=conversation_id, role="user", content=message, sources=[], created_at=asked_at),
            ChatMessage(id=str(uuid4()), conversation_id=conversation_id, role="assistant", content=result["answer"], sources=result["sources"], created_at=answered_at),
        ])
        conversation.updated_at = answered_at
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
        logger.exception("Lỗi MySQL khi lưu hội thoại")
        raise HTTPException(status_code=503, detail="Không thể lưu hội thoại vào MySQL") from exc
    except Exception as exc:
        # Chi tiết lỗi (đường dẫn, cấu hình, thông điệp thư viện) chỉ ghi vào log máy chủ.
        logger.exception("Lỗi khi truy vấn model local")
        raise HTTPException(
            status_code=503,
            detail="Không thể truy vấn model local. Kiểm tra Ollama đang chạy và đã tải đủ model.",
        ) from exc
