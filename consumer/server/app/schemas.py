from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    phone: str = Field(min_length=1, max_length=20)


class CouponOut(BaseModel):
    code: str
    title: str
    amountYuan: int
    thresholdYuan: int
    expiresAt: str


class RegisterOut(BaseModel):
    phone: str
    alreadyClaimed: bool
    coupon: CouponOut


class CampaignOut(BaseModel):
    shop: str
    amountYuan: int
    thresholdYuan: int
    validDays: int
