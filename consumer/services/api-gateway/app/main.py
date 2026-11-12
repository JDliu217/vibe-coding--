import json
import logging
import re

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from common.config import setting
from common.errors import ApiError, install_error_handlers
from common.security import decode_token
from common.trace import install_trace

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="鲜拾网关", version="1.0.0")
install_trace(app)
install_error_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC = {
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/login"),
    ("GET", "/api/catalog/categories"),
    ("GET", "/api/catalog/products"),
    ("GET", "/api/health"),
}
ROUTES = [
    ("/api/admin/products", "CATALOG_URL", "http://127.0.0.1:8092", "/admin/products"),
    ("/api/admin/inventory", "INVENTORY_URL", "http://127.0.0.1:8093", "/admin/inventory"),
    ("/api/admin/orders", "ORDER_URL", "http://127.0.0.1:8094", "/admin/orders"),
    ("/api/auth", "AUTH_URL", "http://127.0.0.1:8091", "/auth"),
    ("/api/catalog", "CATALOG_URL", "http://127.0.0.1:8092", "/catalog"),
    ("/api/orders", "ORDER_URL", "http://127.0.0.1:8094", "/orders"),
    ("/api/inventory", "INVENTORY_URL", "http://127.0.0.1:8093", "/inventory"),
]


def is_public(method: str, path: str) -> bool:
    if (method, path) in PUBLIC:
        return True
    return method == "GET" and re.fullmatch(r"/api/catalog/products/\d+", path) is not None


def authorize(request: Request, path: str) -> None:
    if is_public(request.method, path):
        return
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise ApiError(401, "UNAUTHORIZED", "请先登录")
    claims = decode_token(header.split(" ", 1)[1].strip())
    if path.startswith("/api/admin") and claims.get("role") != "admin":
        raise ApiError(403, "FORBIDDEN", "需要管理员权限")


def match_route(path: str) -> tuple[str, str] | None:
    for prefix, env_name, default, upstream_prefix in ROUTES:
        if path == prefix or path.startswith(prefix + "/"):
            base = setting(env_name, default).rstrip("/")
            suffix = path[len(prefix) :]
            return base + upstream_prefix + suffix, base
    return None


def service_base(env_name: str, default: str) -> str:
    return setting(env_name, default).rstrip("/")


async def enrich_stock(request: Request, payload: dict) -> dict:
    items = payload["items"] if isinstance(payload.get("items"), list) else [payload]
    ids = [str(item["id"]) for item in items if "id" in item]
    if not ids:
        return payload
    url = service_base("INVENTORY_URL", "http://127.0.0.1:8093") + "/internal/stocks?ids=" + ",".join(ids)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                url,
                headers={
                    "x-internal-token": setting("INTERNAL_TOKEN", "dev-internal-token"),
                    "x-request-id": request.state.trace_id,
                },
            )
    except httpx.HTTPError as exc:
        raise ApiError(503, "INVENTORY_UNAVAILABLE", "库存服务不可用") from exc
    if response.status_code >= 400:
        raise ApiError(503, "INVENTORY_UNAVAILABLE", "库存服务不可用")
    stocks = {item["productId"]: item for item in response.json()["items"]}
    for item in items:
        stock = stocks.get(item.get("id"), {})
        item["availableQuantity"] = stock.get("availableQuantity", 0)
        item["reservedQuantity"] = stock.get("reservedQuantity", 0)
    return payload


async def proxy(request: Request, url: str) -> Response:
    trace_id = request.state.trace_id
    headers = {"x-request-id": trace_id}
    if authorization := request.headers.get("authorization"):
        headers["authorization"] = authorization
    if idem := request.headers.get("idempotency-key"):
        headers["idempotency-key"] = idem
    body = await request.body()
    timeout = 20.0 if request.method == "POST" and request.url.path == "/api/orders" else 5.0
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream = await client.request(
                request.method,
                url,
                params=request.query_params,
                content=body,
                headers=headers,
            )
    except httpx.TimeoutException as exc:
        raise ApiError(503, "UPSTREAM_TIMEOUT", "下游服务响应超时") from exc
    except httpx.HTTPError as exc:
        raise ApiError(503, "UPSTREAM_UNAVAILABLE", "下游服务不可用") from exc
    media = upstream.headers.get("content-type", "application/json")
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=media.split(";")[0],
        headers={"x-request-id": trace_id},
    )


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "gateway"}


@app.get("/api/health")
async def api_health(request: Request) -> dict:
    targets = [
        ("auth", service_base("AUTH_URL", "http://127.0.0.1:8091")),
        ("catalog", service_base("CATALOG_URL", "http://127.0.0.1:8092")),
        ("inventory", service_base("INVENTORY_URL", "http://127.0.0.1:8093")),
        ("order", service_base("ORDER_URL", "http://127.0.0.1:8094")),
    ]
    services = []
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            for name, base in targets:
                try:
                    response = await client.get(base + "/health")
                    services.append({"name": name, "ok": response.status_code == 200})
                except httpx.HTTPError:
                    services.append({"name": name, "ok": False})
    except httpx.HTTPError:
        services = [{"name": name, "ok": False} for name, _ in targets]
    return {"ok": all(item["ok"] for item in services), "traceId": request.state.trace_id, "services": services}


@app.get("/api/admin/overview")
async def overview(request: Request):
    authorize(request, "/api/admin/overview")
    trace_id = request.state.trace_id
    headers = {"authorization": request.headers.get("authorization", ""), "x-request-id": trace_id}
    targets = {
        "catalog": service_base("CATALOG_URL", "http://127.0.0.1:8092") + "/admin/metrics",
        "inventory": service_base("INVENTORY_URL", "http://127.0.0.1:8093") + "/admin/metrics",
        "orders": service_base("ORDER_URL", "http://127.0.0.1:8094") + "/admin/metrics",
    }
    payload = {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for name, url in targets.items():
                response = await client.get(url, headers=headers)
                if response.status_code >= 400:
                    return JSONResponse(
                        status_code=response.status_code,
                        content=response.json(),
                        headers={"x-request-id": trace_id},
                    )
                payload[name] = response.json()
    except httpx.TimeoutException as exc:
        raise ApiError(503, "UPSTREAM_TIMEOUT", "统计服务响应超时") from exc
    except httpx.HTTPError as exc:
        raise ApiError(503, "UPSTREAM_UNAVAILABLE", "统计服务不可用") from exc
    return payload


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def gateway(path: str, request: Request):
    full = "/api/" + path
    authorize(request, full)
    matched = match_route(full)
    if matched is None:
        raise ApiError(404, "NOT_FOUND", "接口不存在")
    response = await proxy(request, matched[0])
    catalog_read = request.method == "GET" and (
        full == "/api/catalog/products"
        or full == "/api/admin/products"
        or re.fullmatch(r"/api/catalog/products/\d+", full) is not None
    )
    if catalog_read and response.status_code < 400:
        payload = json.loads(response.body)
        await enrich_stock(request, payload)
        return JSONResponse(payload, headers={"x-request-id": request.state.trace_id})
    return response
