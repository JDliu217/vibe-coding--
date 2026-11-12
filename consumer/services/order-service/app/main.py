import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.flow import change_status, create_order, order_payload, reconcile
from common.db import get_db
from common.errors import ApiError, install_error_handlers
from common.models import Order
from common.security import bearer_user, require_admin, require_internal
from common.trace import install_trace

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="鲜拾订单服务", version="1.0.0")
install_trace(app)
install_error_handlers(app)


class OrderItemIn(BaseModel):
    productId: int
    quantity: int = Field(ge=1, le=99)


class OrderIn(BaseModel):
    items: list[OrderItemIn]


def visible_order(db: Session, order_id: int, actor_id: int, role: str) -> Order:
    order = db.get(Order, order_id)
    if order is None or (role != "admin" and order.user_id != actor_id):
        raise ApiError(404, "ORDER_NOT_FOUND", "订单不存在")
    return order


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "order"}


@app.post("/orders", status_code=201)
def place_order(body: OrderIn, request: Request, db: Session = Depends(get_db)):
    user = bearer_user(request)
    status, payload = create_order(
        db,
        int(user["sub"]),
        [item.model_dump() for item in body.items],
        request.headers.get("idempotency-key", ""),
        request.state.trace_id,
    )
    return JSONResponse(status_code=status, content=payload)


@app.get("/orders/my")
def my_orders(request: Request, db: Session = Depends(get_db)) -> dict:
    user = bearer_user(request)
    rows = db.scalars(select(Order).where(Order.user_id == int(user["sub"])).order_by(Order.id.desc())).all()
    return {"items": [order_payload(db, row) for row in rows]}


@app.get("/orders/{order_id}")
def order_detail(order_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    user = bearer_user(request)
    order = visible_order(db, order_id, int(user["sub"]), user.get("role", "user"))
    return order_payload(db, order)


@app.post("/orders/{order_id}/complete")
def complete_order(order_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    user = bearer_user(request)
    order = db.get(Order, order_id)
    if order is None:
        raise ApiError(404, "ORDER_NOT_FOUND", "订单不存在")
    return change_status(db, order, int(user["sub"]), user.get("role", "user"), "completed", request.state.trace_id)


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    user = bearer_user(request)
    order = db.get(Order, order_id)
    if order is None:
        raise ApiError(404, "ORDER_NOT_FOUND", "订单不存在")
    return change_status(db, order, int(user["sub"]), user.get("role", "user"), "cancelled", request.state.trace_id)


@app.get("/admin/orders")
def admin_orders(request: Request, status: str | None = None, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    query = select(Order).order_by(Order.id.desc())
    if status:
        query = query.where(Order.status == status)
    rows = db.scalars(query.limit(200)).all()
    return {"items": [order_payload(db, row) for row in rows]}


@app.get("/admin/orders/{order_id}")
def admin_order(order_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    user = require_admin(request)
    order = visible_order(db, order_id, int(user["sub"]), "admin")
    return order_payload(db, order)


@app.get("/admin/metrics")
def metrics(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    rows = db.execute(select(Order.status, func.count()).group_by(Order.status)).all()
    counts = {status: count for status, count in rows}
    return {
        "byStatus": counts,
        "orderCount": sum(counts.values()),
        "createdCount": counts.get("created", 0) + counts.get("completed", 0),
    }


@app.post("/internal/recover")
def recover(request: Request, db: Session = Depends(get_db)) -> dict:
    require_internal(request)
    return reconcile(db, request.state.trace_id)
