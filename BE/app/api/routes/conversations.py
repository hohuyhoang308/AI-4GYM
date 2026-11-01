from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.auth import current_user
from app.db.models import ChatMessage, Conversation, User
from app.db.session import get_db, utc_now


router = APIRouter(prefix="/conversations", tags=["conversations"])


class RenamePayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)


def serialize_conversation(conversation: Conversation) -> dict:
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat() + "Z",
        "updated_at": conversation.updated_at.isoformat() + "Z",
    }


def serialize_message(message: ChatMessage) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "sources": message.sources,
        "created_at": message.created_at.isoformat() + "Z",
    }


def owned_conversation(db: Session, user: User, conversation_id: str) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return conversation


@router.get("")
def list_conversations(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    conversations = db.scalars(
        select(Conversation).where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc()).limit(100)
    ).all()
    return [serialize_conversation(item) for item in conversations]


@router.get("/{conversation_id}")
def conversation_detail(conversation_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    conversation = owned_conversation(db, user, conversation_id)
    messages = db.scalars(
        select(ChatMessage).where(ChatMessage.conversation_id == conversation.id).order_by(ChatMessage.created_at, ChatMessage.id)
    ).all()
    return {**serialize_conversation(conversation), "messages": [serialize_message(item) for item in messages]}


@router.patch("/{conversation_id}")
def rename_conversation(conversation_id: str, payload: RenamePayload, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    conversation = owned_conversation(db, user, conversation_id)
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Tên hội thoại không được trống")
    conversation.title = title
    conversation.updated_at = utc_now()
    db.commit()
    return serialize_conversation(conversation)


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    conversation = owned_conversation(db, user, conversation_id)
    db.delete(conversation)
    db.commit()
