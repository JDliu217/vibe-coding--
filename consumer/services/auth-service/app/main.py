import logging
import re
from datetime import datetime

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from common.db import get_db
from common.errors import ApiError, install_error_handlers
from common.models import AuthEvent, User
from common.security import bearer_user, create_token, hash_password, verify_password
from common.trace import install_trace

logging.basicConfig(level=logging.INFO)
PHONE = re.compile(r"^1[3-9]\d{9}$")
app = FastAPI(title="鲜拾鉴权服务", version="1.0.0")
install_trace(app)
install_error_handlers(app)


class RegisterIn(BaseModel):
    phone: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=1, max_length=72)
    email: str | None = None
    nickname: str | None = None


class LoginIn(BaseModel):
    phone: str
    password: str


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def user_out(user: User) -> dict:
    return {
        "id": user.id,
        "phone": user.phone,
        "email": user.email,
        "nickname": user.nickname,
        "role": user.role,
    }


def clean_phone(phone: str) -> str:
    compact = "".join(phone.split())
    if not PHONE.fullmatch(compact):
        raise ApiError(400, "INVALID_PHONE", "请输入 11 位手机号")
    return compact


def record(db: Session, phone: str, action: str, trace_id: str, user_id: int | None) -> None:
    db.add(AuthEvent(user_id=user_id, phone=phone, action=action, trace_id=trace_id, created_at=now()))


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "auth"}


@app.post("/auth/register", status_code=201)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)) -> dict:
    phone = clean_phone(body.phone)
    if len(body.password) < 6:
        raise ApiError(400, "WEAK_PASSWORD", "密码至少 6 位")
    if db.scalar(select(User.id).where(User.phone == phone)):
        raise ApiError(409, "PHONE_TAKEN", "这个手机号已经注册")
    moment = now()
    user = User(
        phone=phone,
        email=(body.email or "").strip() or None,
        nickname=(body.nickname or "").strip() or None,
        password_hash=hash_password(body.password),
        role="user",
        created_at=moment,
        updated_at=moment,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "PHONE_TAKEN", "这个手机号已经注册") from None
    record(db, phone, "register", request.state.trace_id, user.id)
    db.commit()
    return {"user": user_out(user)}


@app.post("/auth/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)) -> dict:
    phone = clean_phone(body.phone)
    user = db.scalar(select(User).where(User.phone == phone))
    if user is None or not verify_password(body.password, user.password_hash or ""):
        record(db, phone, "login_failed", request.state.trace_id, user.id if user else None)
        db.commit()
        raise ApiError(401, "INVALID_CREDENTIALS", "手机号或密码不正确")
    record(db, phone, "login", request.state.trace_id, user.id)
    db.commit()
    return {"accessToken": create_token(user.id, user.role, user.phone), "user": user_out(user)}


@app.get("/auth/me")
def me(request: Request, db: Session = Depends(get_db)) -> dict:
    claims = bearer_user(request)
    user = db.get(User, int(claims["sub"]))
    if user is None:
        raise ApiError(401, "UNAUTHORIZED", "用户不存在")
    return {"user": user_out(user)}
