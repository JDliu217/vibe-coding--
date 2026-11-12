import hashlib
import json
from datetime import datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from common.config import setting
from common.errors import ApiError
from common.models import IdempotencyKey, Order, OrderEvent, OrderItem


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def body_hash(items: list[dict]) -> str:
    normalized = sorted((int(item["productId"]), int(item["quantity"])) for item in items)
    raw = json.dumps(normalized, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def internal_headers(trace_id: str) -> dict:
    return {
        "x-internal-token": setting("INTERNAL_TOKEN", "dev-internal-token"),
        "x-request-id": trace_id,
    }


def order_payload(session: Session, order: Order) -> dict:
    items = session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    return {
        "id": order.id,
        "userId": order.user_id,
        "status": order.status,
        "totalCents": order.total_cents,
        "traceId": order.trace_id,
        "createdAt": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updatedAt": order.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "items": [
            {
                "productId": item.product_id,
                "productName": item.product_name,
                "spec": item.spec,
                "unitPriceCents": item.unit_price_cents,
                "quantity": item.quantity,
            }
            for item in items
        ],
    }


def transition(session: Session, order: Order, status: str, trace_id: str, detail: str) -> None:
    previous = order.status
    order.status = status
    order.updated_at = now()
    session.add(
        OrderEvent(
            order_id=order.id,
            from_status=previous,
            to_status=status,
            trace_id=trace_id,
            detail=detail,
            created_at=now(),
        )
    )


def store_response(record: IdempotencyKey, status_code: int, payload: dict) -> None:
    record.status_code = status_code
    record.response_json = payload


def fetch_products(product_ids: list[int], trace_id: str) -> dict[int, dict]:
    url = setting("CATALOG_URL", "http://127.0.0.1:8092") + "/internal/products/query"
    try:
        response = httpx.post(url, json={"ids": product_ids}, headers=internal_headers(trace_id), timeout=8.0)
    except httpx.TimeoutException as exc:
        raise ApiError(503, "CATALOG_TIMEOUT", "商品服务响应超时，请用同一幂等标识重试") from exc
    except httpx.HTTPError as exc:
        raise ApiError(503, "CATALOG_UNAVAILABLE", "商品服务不可用") from exc
    if response.status_code >= 500:
        raise ApiError(503, "CATALOG_UNAVAILABLE", "商品服务不可用")
    return {item["id"]: item for item in response.json()["items"]}


def inventory_call(path: str, trace_id: str, payload: dict | None = None) -> dict:
    url = setting("INVENTORY_URL", "http://127.0.0.1:8093") + path
    try:
        response = httpx.post(url, json=payload or {}, headers=internal_headers(trace_id), timeout=15.0)
    except httpx.TimeoutException as exc:
        raise ApiError(503, "INVENTORY_TIMEOUT", "库存服务响应超时，请用同一幂等标识重试") from exc
    except httpx.HTTPError as exc:
        raise ApiError(503, "INVENTORY_UNAVAILABLE", "库存服务不可用") from exc
    if response.status_code >= 500:
        raise ApiError(503, "INVENTORY_UNAVAILABLE", "库存服务不可用")
    if response.status_code >= 400:
        body = response.json().get("error", {})
        raise ApiError(response.status_code, body.get("code", "INVENTORY_REJECTED"), body.get("message", "库存操作失败"))
    return response.json()


def reservation_status(order_id: int, trace_id: str) -> str | None:
    url = setting("INVENTORY_URL", "http://127.0.0.1:8093") + f"/internal/reservations/{order_id}"
    try:
        response = httpx.get(url, headers=internal_headers(trace_id), timeout=8.0)
    except httpx.HTTPError as exc:
        raise ApiError(503, "INVENTORY_UNAVAILABLE", "库存服务不可用") from exc
    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise ApiError(503, "INVENTORY_UNAVAILABLE", "库存服务不可用")
    return response.json()["status"]


def fail_order(session: Session, record: IdempotencyKey, order: Order, trace_id: str, message: str) -> tuple[int, dict]:
    if order.status == "creating":
        transition(session, order, "failed", trace_id, message)
    payload = {"error": {"code": "ORDER_FAILED", "message": message, "traceId": trace_id}, "order": order_payload(session, order)}
    store_response(record, 409, payload)
    session.commit()
    return 409, payload


def finish_created(session: Session, record: IdempotencyKey, order: Order, trace_id: str) -> tuple[int, dict]:
    if order.status == "creating":
        transition(session, order, "created", trace_id, "库存已确认")
    payload = order_payload(session, order)
    store_response(record, 201, payload)
    session.commit()
    return 201, payload


def create_order(session: Session, user_id: int, items: list[dict], idem_key: str, trace_id: str) -> tuple[int, dict]:
    key = idem_key.strip()
    if not key or len(key) > 64:
        raise ApiError(400, "IDEMPOTENCY_KEY_REQUIRED", "请提供不超过 64 位的 Idempotency-Key")
    if not items:
        raise ApiError(400, "EMPTY_ORDER", "订单里没有商品")
    digest = body_hash(items)
    record = session.scalar(
        select(IdempotencyKey).where(IdempotencyKey.user_id == user_id, IdempotencyKey.idem_key == key)
    )
    if record and record.body_hash != digest:
        raise ApiError(409, "IDEMPOTENCY_CONFLICT", "同一幂等标识对应了不同的订单内容")
    if record and record.response_json and record.status_code:
        order = session.get(Order, record.order_id)
        if order and order.status != "creating":
            return record.status_code, record.response_json
    if record is None:
        moment = now()
        order = Order(
            user_id=user_id,
            status="creating",
            total_cents=0,
            trace_id=trace_id,
            created_at=moment,
            updated_at=moment,
        )
        session.add(order)
        session.flush()
        record = IdempotencyKey(
            user_id=user_id,
            idem_key=key,
            body_hash=digest,
            order_id=order.id,
            created_at=moment,
        )
        session.add(record)
        session.add(
            OrderEvent(
                order_id=order.id,
                from_status=None,
                to_status="creating",
                trace_id=trace_id,
                detail="开始创建订单",
                created_at=moment,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            record = session.scalar(
                select(IdempotencyKey).where(IdempotencyKey.user_id == user_id, IdempotencyKey.idem_key == key)
            )
            if record is None:
                raise
            if record.body_hash != digest:
                raise ApiError(409, "IDEMPOTENCY_CONFLICT", "同一幂等标识对应了不同的订单内容") from None
            order = session.get(Order, record.order_id)
    else:
        order = session.get(Order, record.order_id)

    if order is None:
        raise ApiError(500, "ORDER_MISSING", "订单记录丢失")
    if order.status != "creating" and record.response_json:
        return record.status_code or 200, record.response_json

    products = fetch_products(sorted({int(item["productId"]) for item in items}), trace_id)
    for item in items:
        product = products.get(int(item["productId"]))
        quantity = int(item["quantity"])
        if quantity < 1 or quantity > 99:
            return fail_order(session, record, order, trace_id, "购买数量需要在 1 到 99 之间")
        if product is None or product["status"] != "on":
            return fail_order(session, record, order, trace_id, "商品不存在或已下架")

    reserved = reservation_status(order.id, trace_id)
    if reserved is None:
        try:
            inventory_call(
                "/internal/reservations",
                trace_id,
                {"orderId": order.id, "items": [{"productId": int(item["productId"]), "quantity": int(item["quantity"])} for item in items]},
            )
        except ApiError as exc:
            if exc.code in ("INSUFFICIENT_STOCK", "STOCK_NOT_FOUND", "INVALID_QUANTITY"):
                return fail_order(session, record, order, trace_id, exc.message)
            raise
        reserved = "reserved"

    existing_items = session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    if not existing_items:
        total = 0
        for item in items:
            product = products[int(item["productId"])]
            quantity = int(item["quantity"])
            total += product["priceCents"] * quantity
            session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product["id"],
                    product_name=product["name"],
                    spec=product["spec"],
                    unit_price_cents=product["priceCents"],
                    quantity=quantity,
                )
            )
        order.total_cents = total
        order.updated_at = now()
        session.commit()

    if reserved == "reserved":
        inventory_call(f"/internal/reservations/{order.id}/confirm", trace_id)
    elif reserved == "released":
        return fail_order(session, record, order, trace_id, "库存预占已释放")
    return finish_created(session, record, order, trace_id)


def change_status(session: Session, order: Order, actor_id: int, role: str, target: str, trace_id: str) -> dict:
    if role != "admin" and order.user_id != actor_id:
        raise ApiError(403, "FORBIDDEN", "不能操作别人的订单")
    if target == "completed":
        if order.status == "completed":
            return order_payload(session, order)
        if order.status != "created":
            raise ApiError(409, "INVALID_TRANSITION", "只有已创建的订单可以完成")
        transition(session, order, "completed", trace_id, "演示场景确认完成")
    elif target == "cancelled":
        if order.status == "cancelled":
            return order_payload(session, order)
        if order.status != "created":
            raise ApiError(409, "INVALID_TRANSITION", "只有已创建的订单可以取消")
        inventory_call(f"/internal/reservations/{order.id}/release", trace_id)
        transition(session, order, "cancelled", trace_id, "取消并恢复库存")
    else:
        raise ApiError(400, "INVALID_TRANSITION", "不支持的订单状态")
    session.commit()
    return order_payload(session, order)


def reconcile(session: Session, trace_id: str) -> dict:
    rows = session.scalars(select(Order).where(Order.status == "creating")).all()
    finished = 0
    failed = 0
    for order in rows:
        record = session.scalar(select(IdempotencyKey).where(IdempotencyKey.order_id == order.id))
        status = reservation_status(order.id, trace_id)
        item_count = session.scalar(select(func.count()).select_from(OrderItem).where(OrderItem.order_id == order.id)) or 0
        if status is None or (status == "reserved" and item_count == 0) or status == "released":
            if status == "reserved":
                inventory_call(f"/internal/reservations/{order.id}/release", trace_id)
            if record:
                fail_order(session, record, order, trace_id, "恢复任务结束未完成的订单")
            elif order.status == "creating":
                transition(session, order, "failed", trace_id, "恢复任务结束未完成的订单")
                session.commit()
            failed += 1
        elif status in ("reserved", "confirmed") and item_count:
            if status == "reserved":
                inventory_call(f"/internal/reservations/{order.id}/confirm", trace_id)
            if record:
                finish_created(session, record, order, trace_id)
            elif order.status == "creating":
                transition(session, order, "created", trace_id, "恢复任务确认库存")
                session.commit()
            finished += 1
    return {"finished": finished, "failed": failed}
