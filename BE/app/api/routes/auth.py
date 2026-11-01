from datetime import timedelta
from hashlib import sha256
import secrets

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import LoginSession, User
from app.db.session import get_db, utc_now


router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE_NAME = "ai4gym_session"
SESSION_MAX_AGE = 7 * 24 * 60 * 60
password_hash = PasswordHash.recommended()


class RegisterPayload(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


def public_user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "created_at": user.created_at.isoformat() + "Z"}


def _issue_session(response: Response, db: Session, user: User) -> None:
    token = secrets.token_urlsafe(32)
    db.add(LoginSession(
        token_hash=sha256(token.encode()).hexdigest(),
        user_id=user.id,
        expires_at=utc_now() + timedelta(seconds=SESSION_MAX_AGE),
    ))
    db.commit()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def optional_user(
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None
    login_session = db.get(LoginSession, sha256(token.encode()).hexdigest())
    if login_session is None:
        return None
    if login_session.expires_at <= utc_now():
        db.delete(login_session)
        db.commit()
        return None
    return db.get(User, login_session.user_id)


def current_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cần đăng nhập để xem lịch sử")
    return user


@router.post("/register", status_code=201)
def register(payload: RegisterPayload, response: Response, db: Session = Depends(get_db)) -> dict:
    email = str(payload.email).strip().lower()
    name = payload.display_name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Tên hiển thị cần ít nhất 2 ký tự")
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Email này đã được sử dụng")
    user = User(email=email, display_name=name, password_hash=password_hash.hash(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email này đã được sử dụng") from exc
    db.refresh(user)
    _issue_session(response, db, user)
    return public_user(user)


@router.post("/login")
def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)) -> dict:
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    _issue_session(response, db, user)
    return public_user(user)


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return public_user(user)


@router.post("/logout")
def logout(
    response: Response,
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> dict:
    if token:
        login_session = db.get(LoginSession, sha256(token.encode()).hexdigest())
        if login_session:
            db.delete(login_session)
            db.commit()
    response.delete_cookie(key=COOKIE_NAME, path="/", secure=settings.cookie_secure, samesite="lax")
    return {"ok": True}
