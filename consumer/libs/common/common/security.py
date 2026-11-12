from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Request

from common.config import setting
from common.errors import ApiError

PHONE_PATTERN_SOURCE = r"^1[3-9]\d{9}$"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_id: int, role: str, phone: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "phone": phone,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
    }
    return jwt.encode(payload, setting("JWT_SECRET", "dev-only-change-me"), algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, setting("JWT_SECRET", "dev-only-change-me"), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ApiError(401, "UNAUTHORIZED", "登录已失效，请重新登录") from exc


def bearer_user(request: Request) -> dict:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise ApiError(401, "UNAUTHORIZED", "请先登录")
    return decode_token(header.split(" ", 1)[1].strip())


def require_admin(request: Request) -> dict:
    user = bearer_user(request)
    if user.get("role") != "admin":
        raise ApiError(403, "FORBIDDEN", "需要管理员权限")
    return user


def require_internal(request: Request) -> None:
    expected = setting("INTERNAL_TOKEN", "dev-internal-token")
    if request.headers.get("x-internal-token") != expected:
        raise ApiError(401, "UNAUTHORIZED", "内部调用未授权")
