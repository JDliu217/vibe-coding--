from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.errors import ApiError
from common.models import InventoryAdjustment, InventoryItem, InventoryReservation, InventoryReservationItem


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def stock_out(row: InventoryItem) -> dict:
    return {
        "productId": row.product_id,
        "availableQuantity": row.available_quantity,
        "reservedQuantity": row.reserved_quantity,
    }


def lock_items(session: Session, product_ids: list[int]) -> dict[int, InventoryItem]:
    rows = session.scalars(
        select(InventoryItem)
        .where(InventoryItem.product_id.in_(product_ids))
        .order_by(InventoryItem.product_id)
        .with_for_update()
    ).all()
    return {row.product_id: row for row in rows}


def ensure_item(session: Session, product_id: int, available: int) -> InventoryItem:
    row = session.scalar(select(InventoryItem).where(InventoryItem.product_id == product_id).with_for_update())
    if row:
        return row
    if available < 0:
        raise ApiError(400, "INVALID_STOCK", "可用库存不能为负")
    row = InventoryItem(
        product_id=product_id,
        available_quantity=available,
        reserved_quantity=0,
        updated_at=now(),
    )
    session.add(row)
    session.flush()
    return row


def reservation_lines(session: Session, reservation: InventoryReservation) -> list[InventoryReservationItem]:
    return list(
        session.scalars(
            select(InventoryReservationItem).where(InventoryReservationItem.reservation_id == reservation.id)
        ).all()
    )


def reserve(session: Session, order_id: int, items: list[dict]) -> InventoryReservation:
    existing = session.scalar(
        select(InventoryReservation).where(InventoryReservation.order_id == order_id).with_for_update()
    )
    if existing:
        if existing.status in ("reserved", "confirmed"):
            return existing
        raise ApiError(409, "RESERVATION_CLOSED", "这笔预占已经结束")

    needed: dict[int, int] = {}
    for item in items:
        product_id = int(item["productId"])
        quantity = int(item["quantity"])
        if quantity <= 0:
            raise ApiError(400, "INVALID_QUANTITY", "购买数量必须大于 0")
        needed[product_id] = needed.get(product_id, 0) + quantity
    rows = lock_items(session, sorted(needed))
    if len(rows) != len(needed):
        raise ApiError(409, "STOCK_NOT_FOUND", "部分商品没有库存记录")
    for product_id, quantity in needed.items():
        if rows[product_id].available_quantity < quantity:
            raise ApiError(409, "INSUFFICIENT_STOCK", "库存不足")
    moment = now()
    for product_id, quantity in needed.items():
        row = rows[product_id]
        row.available_quantity -= quantity
        row.reserved_quantity += quantity
        row.updated_at = moment
    reservation = InventoryReservation(order_id=order_id, status="reserved", created_at=moment, updated_at=moment)
    session.add(reservation)
    session.flush()
    for product_id, quantity in needed.items():
        session.add(
            InventoryReservationItem(reservation_id=reservation.id, product_id=product_id, quantity=quantity)
        )
    session.commit()
    return reservation


def confirm(session: Session, order_id: int) -> InventoryReservation:
    reservation = session.scalar(
        select(InventoryReservation).where(InventoryReservation.order_id == order_id).with_for_update()
    )
    if reservation is None:
        raise ApiError(404, "RESERVATION_NOT_FOUND", "没有找到库存预占")
    if reservation.status == "confirmed":
        session.commit()
        return reservation
    if reservation.status != "reserved":
        raise ApiError(409, "RESERVATION_CLOSED", "这笔预占不能确认")
    lines = reservation_lines(session, reservation)
    rows = lock_items(session, sorted(line.product_id for line in lines))
    moment = now()
    for line in lines:
        row = rows[line.product_id]
        if row.reserved_quantity < line.quantity:
            raise ApiError(409, "RESERVATION_MISMATCH", "预占数量异常")
        row.reserved_quantity -= line.quantity
        row.updated_at = moment
    reservation.status = "confirmed"
    reservation.updated_at = moment
    session.commit()
    return reservation


def release(session: Session, order_id: int) -> InventoryReservation:
    reservation = session.scalar(
        select(InventoryReservation).where(InventoryReservation.order_id == order_id).with_for_update()
    )
    if reservation is None:
        raise ApiError(404, "RESERVATION_NOT_FOUND", "没有找到库存预占")
    if reservation.status == "released":
        session.commit()
        return reservation
    lines = reservation_lines(session, reservation)
    rows = lock_items(session, sorted(line.product_id for line in lines))
    moment = now()
    for line in lines:
        row = rows[line.product_id]
        if reservation.status == "reserved":
            if row.reserved_quantity < line.quantity:
                raise ApiError(409, "RESERVATION_MISMATCH", "预占数量异常")
            row.reserved_quantity -= line.quantity
            row.available_quantity += line.quantity
        elif reservation.status == "confirmed":
            row.available_quantity += line.quantity
        else:
            raise ApiError(409, "RESERVATION_CLOSED", "这笔预占不能释放")
        row.updated_at = moment
    reservation.status = "released"
    reservation.updated_at = moment
    session.commit()
    return reservation


def adjust(session: Session, product_id: int, available: int, reason: str, actor_id: int | None) -> InventoryItem:
    if available < 0:
        raise ApiError(400, "INVALID_STOCK", "可用库存不能为负")
    row = session.scalar(select(InventoryItem).where(InventoryItem.product_id == product_id).with_for_update())
    if row is None:
        raise ApiError(404, "STOCK_NOT_FOUND", "没有库存记录")
    before = row.available_quantity
    row.available_quantity = available
    row.updated_at = now()
    session.add(
        InventoryAdjustment(
            product_id=product_id,
            available_before=before,
            available_after=available,
            reason=reason.strip() or "管理员调整",
            actor_id=actor_id,
            created_at=now(),
        )
    )
    session.commit()
    return row
