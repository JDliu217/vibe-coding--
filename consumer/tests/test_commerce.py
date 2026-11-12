import threading
import uuid

import httpx

BASE = "http://127.0.0.1:8090"
ADMIN = {"phone": "13800000000", "password": "Admin123456"}
USER = {"phone": "13900001001", "password": "User123456"}


def token(account: dict) -> str:
    response = httpx.post(f"{BASE}/api/auth/login", json=account, timeout=10)
    assert response.status_code == 200, response.text
    return response.json()["accessToken"]


def auth(value: str) -> dict:
    return {"Authorization": f"Bearer {value}"}


def test_register_rejects_duplicate_and_hides_password():
    created = httpx.post(
        f"{BASE}/api/auth/register",
        json={"phone": "13900002002", "password": "User123456", "nickname": "测试"},
        timeout=10,
    )
    assert created.status_code in (201, 409)
    if created.status_code == 201:
        assert "password" not in created.text.lower() or "passwordHash" not in created.text
        assert created.json()["user"]["role"] == "user"
    again = httpx.post(f"{BASE}/api/auth/register", json={"phone": "13900002002", "password": "User123456"}, timeout=10)
    assert again.status_code == 409


def test_user_cannot_open_admin_metrics():
    value = token(USER)
    response = httpx.get(f"{BASE}/api/admin/overview", headers=auth(value), timeout=10)
    assert response.status_code == 403


def test_order_uses_snapshot_and_blocks_other_user():
    admin = token(ADMIN)
    user = token(USER)
    products = httpx.get(f"{BASE}/api/catalog/products?pageSize=1", timeout=10).json()["items"]
    product = products[0]
    if product["availableQuantity"] < 1:
        httpx.patch(
            f"{BASE}/api/inventory/{product['id']}",
            headers=auth(admin),
            json={"availableQuantity": 5, "reason": "快照测试补库存"},
            timeout=10,
        )
        product = httpx.get(f"{BASE}/api/catalog/products?pageSize=1", timeout=10).json()["items"][0]
    key = uuid.uuid4().hex
    created = httpx.post(
        f"{BASE}/api/orders",
        headers={**auth(user), "Idempotency-Key": key},
        json={"items": [{"productId": product["id"], "quantity": 1}]},
        timeout=10,
    )
    assert created.status_code == 201, created.text
    order = created.json()
    assert order["items"][0]["unitPriceCents"] == product["priceCents"]
    httpx.patch(
        f"{BASE}/api/admin/products/{product['id']}",
        headers=auth(admin),
        json={"priceCents": product["priceCents"] + 100},
        timeout=10,
    )
    again = httpx.get(f"{BASE}/api/orders/{order['id']}", headers=auth(user), timeout=10).json()
    assert again["totalCents"] == order["totalCents"]
    stranger = httpx.post(
        f"{BASE}/api/auth/register",
        json={"phone": "13900002003", "password": "User123456"},
        timeout=10,
    )
    if stranger.status_code == 409:
        stranger_token = token({"phone": "13900002003", "password": "User123456"})
    else:
        login = httpx.post(f"{BASE}/api/auth/login", json={"phone": "13900002003", "password": "User123456"}, timeout=10)
        stranger_token = login.json()["accessToken"]
    hidden = httpx.get(f"{BASE}/api/orders/{order['id']}", headers=auth(stranger_token), timeout=10)
    assert hidden.status_code == 404
    httpx.patch(
        f"{BASE}/api/admin/products/{product['id']}",
        headers=auth(admin),
        json={"priceCents": product["priceCents"]},
        timeout=10,
    )


def test_idempotent_order_and_cancel_restore_once():
    user = token(USER)
    product = httpx.get(f"{BASE}/api/catalog/products?pageSize=50", timeout=10).json()["items"][-1]
    before = product["availableQuantity"]
    key = uuid.uuid4().hex
    body = {"items": [{"productId": product["id"], "quantity": 1}]}
    headers = {**auth(user), "Idempotency-Key": key}
    first = httpx.post(f"{BASE}/api/orders", headers=headers, json=body, timeout=10)
    second = httpx.post(f"{BASE}/api/orders", headers=headers, json=body, timeout=10)
    assert first.status_code == 201, first.text
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    conflict = httpx.post(
        f"{BASE}/api/orders",
        headers=headers,
        json={"items": [{"productId": product["id"], "quantity": 2}]},
        timeout=10,
    )
    assert conflict.status_code == 409
    order_id = first.json()["id"]
    cancel = httpx.post(f"{BASE}/api/orders/{order_id}/cancel", headers=auth(user), timeout=10)
    again = httpx.post(f"{BASE}/api/orders/{order_id}/cancel", headers=auth(user), timeout=10)
    assert cancel.status_code == 200
    assert again.status_code == 200
    assert again.json()["status"] == "cancelled"
    listed = httpx.get(f"{BASE}/api/catalog/products?pageSize=50", timeout=10).json()["items"]
    current = next(item for item in listed if item["id"] == product["id"])
    assert current["availableQuantity"] == before


def test_insufficient_stock_does_not_decrement():
    admin = token(ADMIN)
    user = token(USER)
    product = httpx.get(f"{BASE}/api/catalog/products?pageSize=1", timeout=10).json()["items"][0]
    original = product["availableQuantity"]
    httpx.patch(
        f"{BASE}/api/inventory/{product['id']}",
        headers=auth(admin),
        json={"availableQuantity": 1, "reason": "测试库存不足"},
        timeout=10,
    )
    failed = httpx.post(
        f"{BASE}/api/orders",
            headers={**auth(user), "Idempotency-Key": uuid.uuid4().hex},
        json={"items": [{"productId": product["id"], "quantity": 2}]},
        timeout=10,
    )
    assert failed.status_code == 409
    listed = httpx.get(f"{BASE}/api/catalog/products?q={product['name']}", timeout=10).json()["items"]
    current = next(item for item in listed if item["id"] == product["id"])
    assert current["availableQuantity"] == 1
    httpx.patch(
        f"{BASE}/api/inventory/{product['id']}",
        headers=auth(admin),
        json={"availableQuantity": original, "reason": "恢复测试库存"},
        timeout=10,
    )


def test_concurrent_last_item_allows_one_winner():
    admin = token(ADMIN)
    user = token(USER)
    product = httpx.get(f"{BASE}/api/catalog/products?pageSize=1", timeout=10).json()["items"][0]
    original = product["availableQuantity"]
    httpx.patch(
        f"{BASE}/api/inventory/{product['id']}",
        headers=auth(admin),
        json={"availableQuantity": 1, "reason": "并发测试"},
        timeout=10,
    )
    results = []

    def buy(index: int) -> None:
        response = httpx.post(
            f"{BASE}/api/orders",
            headers={**auth(user), "Idempotency-Key": uuid.uuid4().hex},
            json={"items": [{"productId": product["id"], "quantity": 1}]},
            timeout=10,
        )
        results.append((response.status_code, response.json()))

    threads = [threading.Thread(target=buy, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    codes = [item[0] for item in results]
    assert codes.count(201) == 1
    assert all(code in (201, 409, 503) for code in codes)
    winner = next(item[1]["id"] for item in results if item[0] == 201)
    cancelled = httpx.post(f"{BASE}/api/orders/{winner}/cancel", headers=auth(user), timeout=20)
    assert cancelled.status_code == 200
    httpx.post(
        "http://127.0.0.1:8094/internal/recover",
        headers={"x-internal-token": "dev-internal-token"},
        timeout=20,
    )
    restored = httpx.get(f"{BASE}/api/catalog/products?pageSize=1", timeout=10).json()["items"][0]
    assert restored["id"] == product["id"]
    assert restored["availableQuantity"] == 1
    httpx.patch(
        f"{BASE}/api/inventory/{product['id']}",
        headers=auth(admin),
        json={"availableQuantity": original, "reason": "恢复并发测试"},
        timeout=10,
    )


def test_recover_creating_order_without_stock_change():
    from datetime import datetime
    from common.db import SessionLocal
    from common.models import Order

    user = httpx.get(f"{BASE}/api/auth/me", headers=auth(token(USER)), timeout=10).json()["user"]
    product = httpx.get(f"{BASE}/api/catalog/products?pageSize=1", timeout=10).json()["items"][0]
    before = product["availableQuantity"]
    moment = datetime.now().replace(microsecond=0)
    session = SessionLocal()
    order = Order(user_id=user["id"], status="creating", total_cents=0, trace_id="recover-test", created_at=moment, updated_at=moment)
    session.add(order)
    session.commit()
    order_id = order.id
    session.close()
    recovered = httpx.post(
        "http://127.0.0.1:8094/internal/recover",
        headers={"x-internal-token": "dev-internal-token"},
        timeout=20,
    )
    assert recovered.status_code == 200, recovered.text
    row = SessionLocal()
    saved = row.get(Order, order_id)
    assert saved.status == "failed"
    row.close()
    listed = httpx.get(f"{BASE}/api/catalog/products?q={product['name']}", timeout=10).json()["items"]
    current = next(item for item in listed if item["id"] == product["id"])
    assert current["availableQuantity"] == before
