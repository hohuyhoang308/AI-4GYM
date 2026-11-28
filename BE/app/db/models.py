from datetime import datetime

from sqlalchemy import case, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, utc_now


# MySQL DATETIME mặc định chỉ lưu đến giây. Tin nhắn người dùng và trợ lý được ghi
# trong cùng một request nên cần độ chính xác micro giây (fsp=6) để giữ đúng thứ tự.
Timestamp = DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(Timestamp, default=utc_now, nullable=False)
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class LoginSession(Base):
    __tablename__ = "login_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(Timestamp, default=utc_now, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    user: Mapped[User] = relationship()


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(Timestamp, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(Timestamp, default=utc_now, nullable=False)
    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    __table_args__ = (Index("ix_conversations_user_updated", "user_id", "updated_at"),)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(Timestamp, default=utc_now, nullable=False)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class ChatRequestRecord(Base):
    __tablename__ = "chat_request_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    message_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(Timestamp, default=utc_now, index=True, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "request_id", name="uq_chat_request_user_id"),)


def message_order(descending: bool = False) -> tuple:
    """Khóa sắp xếp tin nhắn: thời điểm tạo, rồi vai trò (user trước assistant).

    Khóa phụ theo vai trò giữ đúng thứ tự cho dữ liệu cũ đã lưu ở độ chính xác giây,
    khi câu hỏi và câu trả lời có cùng created_at. Không dùng id vì id là UUID ngẫu nhiên.
    """
    role_rank = case((ChatMessage.role == "user", 0), else_=1)
    if descending:
        return ChatMessage.created_at.desc(), role_rank.desc()
    return ChatMessage.created_at.asc(), role_rank.asc()
