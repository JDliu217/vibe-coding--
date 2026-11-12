from pydantic import BaseModel, Field


class StartIn(BaseModel):
    reuseIntensity: float = Field(ge=0, le=1)
    batchSize: int = Field(ge=1, le=100)
    intervalMs: int = Field(ge=500, le=30000)


class TickIn(BaseModel):
    reuseIntensity: float = Field(ge=0, le=1)
    batchSize: int = Field(ge=1, le=100)


class StatsOut(BaseModel):
    total: int
    success: int
    failed: int
    rounds: int


class SubmissionOut(BaseModel):
    id: str
    phone: str
    createdAt: str
    deviceId: str
    deviceModel: str
    ip: str
    isp: str
    region: str
    status: str


class StateOut(BaseModel):
    status: str
    batchId: int | None = None
    reuseIntensity: float
    batchSize: int
    intervalMs: int
    stats: StatsOut
    submissions: list[SubmissionOut]
