import re
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Coupon, User
from app.schemas import CampaignOut, CouponOut, RegisterOut

PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
OFFER = {
    "shop": "拾光集市",
    "title": "新人立减券",
    "amount_cent": 2000,
    "threshold_cent": 9900,
    "valid_days": 7,
}


class RegistrationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def campaign() -> CampaignOut:
    return CampaignOut(
        shop=OFFER["shop"],
        amountYuan=OFFER["amount_cent"] // 100,
        thresholdYuan=OFFER["threshold_cent"] // 100,
        validDays=OFFER["valid_days"],
    )


def normalize_phone(phone: str) -> str:
    compact = "".join(phone.split())
    if not PHONE_PATTERN.fullmatch(compact):
        raise RegistrationError("请输入 11 位手机号")
    return compact


def _coupon_out(coupon: Coupon) -> CouponOut:
    return CouponOut(
        code=coupon.code,
        title=coupon.title,
        amountYuan=coupon.amount_cent // 100,
        thresholdYuan=coupon.threshold_cent // 100,
        expiresAt=coupon.expires_at.strftime("%Y-%m-%d"),
    )


def _existing(session: Session, phone: str) -> RegisterOut | None:
    user = session.scalar(select(User).where(User.phone == phone))
    if user is None:
        return None
    coupon = session.scalar(select(Coupon).where(Coupon.user_id == user.id))
    if coupon is None:
        raise RegistrationError("这个手机号已注册，但券没有生成", 500)
    return RegisterOut(phone=user.phone, alreadyClaimed=True, coupon=_coupon_out(coupon))


def _mint_code() -> str:
    return f"SG{secrets.token_hex(4).upper()}"


def register_phone(session: Session, raw_phone: str) -> RegisterOut:
    phone = normalize_phone(raw_phone)
    found = _existing(session, phone)
    if found:
        return found

    now = datetime.now().replace(microsecond=0)
    user = User(phone=phone, created_at=now)
    session.add(user)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        found = _existing(session, phone)
        if found:
            return found
        raise

    coupon = Coupon(
        user_id=user.id,
        code=_mint_code(),
        title=OFFER["title"],
        amount_cent=OFFER["amount_cent"],
        threshold_cent=OFFER["threshold_cent"],
        expires_at=now + timedelta(days=OFFER["valid_days"]),
        created_at=now,
    )
    session.add(coupon)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        found = _existing(session, phone)
        if found:
            return found
        raise
    return RegisterOut(phone=user.phone, alreadyClaimed=False, coupon=_coupon_out(coupon))


def read_registration(session: Session, raw_phone: str) -> RegisterOut:
    phone = normalize_phone(raw_phone)
    found = _existing(session, phone)
    if found is None:
        raise RegistrationError("这个手机号还没有领券", 404)
    return found
