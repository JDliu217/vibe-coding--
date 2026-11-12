from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import apply_schema, get_db
from app.registration import RegistrationError, campaign, read_registration, register_phone
from app.schemas import CampaignOut, RegisterIn, RegisterOut


@asynccontextmanager
async def lifespan(_app: FastAPI):
    apply_schema()
    yield


app = FastAPI(title="拾光集市", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5175", "http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _call(action):
    try:
        return action()
    except RegistrationError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/campaign", response_model=CampaignOut)
def read_campaign() -> CampaignOut:
    return campaign()


@app.post("/api/registrations", response_model=RegisterOut)
def create_registration(body: RegisterIn, db: Session = Depends(get_db)) -> RegisterOut:
    return _call(lambda: register_phone(db, body.phone))


@app.get("/api/registrations/{phone}", response_model=RegisterOut)
def registration(phone: str, db: Session = Depends(get_db)) -> RegisterOut:
    return _call(lambda: read_registration(db, phone))
