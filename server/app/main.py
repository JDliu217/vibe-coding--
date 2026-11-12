from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import ensure_round_count, get_db
from app.registration import RegistrationError, read_state, reset_ledger, run_tick, start_batch, stop_batch
from app.schemas import StartIn, StateOut, TickIn


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_round_count()
    yield


app = FastAPI(title="攻击模拟控制台", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:5174", "http://localhost:5174"],
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


@app.get("/api/state", response_model=StateOut)
def state(db: Session = Depends(get_db)) -> StateOut:
    return read_state(db)


@app.post("/api/batches", response_model=StateOut)
def create_batch(body: StartIn, db: Session = Depends(get_db)) -> StateOut:
    return _call(lambda: start_batch(db, body))


@app.post("/api/batches/{batch_id}/tick", response_model=StateOut)
def tick(batch_id: int, body: TickIn, db: Session = Depends(get_db)) -> StateOut:
    return _call(lambda: run_tick(db, batch_id, body))


@app.post("/api/batches/{batch_id}/stop", response_model=StateOut)
def stop(batch_id: int, db: Session = Depends(get_db)) -> StateOut:
    return stop_batch(db, batch_id)


@app.post("/api/reset", response_model=StateOut)
def reset(db: Session = Depends(get_db)) -> StateOut:
    return reset_ledger(db)
