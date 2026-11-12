import logging

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.stock import adjust, confirm, ensure_item, release, reserve, stock_out
from common.db import get_db
from common.errors import ApiError, install_error_handlers
from common.models import InventoryAdjustment, InventoryItem, InventoryReservation
from common.security import require_admin, require_internal
from common.trace import install_trace

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="鲜拾库存服务", version="1.0.0")
install_trace(app)
install_error_handlers(app)


class ItemIn(BaseModel):
    productId: int
    available: int = Field(ge=0)


class ReserveItem(BaseModel):
    productId: int
    quantity: int = Field(ge=1)


class ReserveIn(BaseModel):
    orderId: int
    items: list[ReserveItem]


class AdjustIn(BaseModel):
    availableQuantity: int = Field(ge=0)
    reason: str = "管理员调整"


def reservation_out(row: InventoryReservation) -> dict:
    return {"orderId": row.order_id, "status": row.status}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "inventory"}


@app.get("/internal/stocks")
def stocks(ids: str, request: Request, db: Session = Depends(get_db)) -> dict:
    require_internal(request)
    product_ids = [int(part) for part in ids.split(",") if part.strip().isdigit()]
    if not product_ids:
        return {"items": []}
    rows = db.scalars(select(InventoryItem).where(InventoryItem.product_id.in_(product_ids))).all()
    return {"items": [stock_out(row) for row in rows]}


@app.post("/internal/items")
def create_item(body: ItemIn, request: Request, db: Session = Depends(get_db)) -> dict:
    require_internal(request)
    row = ensure_item(db, body.productId, body.available)
    db.commit()
    return stock_out(row)


@app.post("/internal/reservations")
def create_reservation(body: ReserveIn, request: Request, db: Session = Depends(get_db)) -> dict:
    require_internal(request)
    row = reserve(db, body.orderId, [item.model_dump() for item in body.items])
    return reservation_out(row)


@app.get("/internal/reservations/{order_id}")
def read_reservation(order_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    require_internal(request)
    row = db.scalar(select(InventoryReservation).where(InventoryReservation.order_id == order_id))
    if row is None:
        raise ApiError(404, "RESERVATION_NOT_FOUND", "没有找到库存预占")
    return reservation_out(row)


@app.post("/internal/reservations/{order_id}/confirm")
def confirm_reservation(order_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    require_internal(request)
    return reservation_out(confirm(db, order_id))


@app.post("/internal/reservations/{order_id}/release")
def release_reservation(order_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    require_internal(request)
    return reservation_out(release(db, order_id))


@app.get("/admin/inventory")
def inventory_list(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    rows = db.scalars(select(InventoryItem).order_by(InventoryItem.product_id)).all()
    return {"items": [stock_out(row) for row in rows]}


@app.get("/admin/inventory/adjustments")
def adjustments(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    rows = db.scalars(select(InventoryAdjustment).order_by(InventoryAdjustment.id.desc()).limit(100)).all()
    return {
        "items": [
            {
                "id": row.id,
                "productId": row.product_id,
                "availableBefore": row.available_before,
                "availableAfter": row.available_after,
                "reason": row.reason,
                "actorId": row.actor_id,
                "createdAt": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for row in rows
        ]
    }


@app.patch("/inventory/{product_id}")
def patch_stock(product_id: int, body: AdjustIn, request: Request, db: Session = Depends(get_db)) -> dict:
    user = require_admin(request)
    row = adjust(db, product_id, body.availableQuantity, body.reason, int(user["sub"]))
    return stock_out(row)


@app.get("/admin/metrics")
def metrics(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    low = db.scalar(
        select(func.count()).select_from(InventoryItem).where(InventoryItem.available_quantity <= 10)
    ) or 0
    return {"lowStockCount": low, "threshold": 10}
