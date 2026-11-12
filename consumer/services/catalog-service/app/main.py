import logging
from datetime import datetime

import httpx
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from common.config import setting
from common.db import get_db
from common.errors import ApiError, install_error_handlers
from common.models import Category, Product
from common.security import require_admin, require_internal
from common.trace import install_trace

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="鲜拾商品服务", version="1.0.0")
install_trace(app)
install_error_handlers(app)


class ProductIn(BaseModel):
    categoryId: int
    name: str = Field(min_length=1, max_length=64)
    spec: str = Field(min_length=1, max_length=64)
    description: str = ""
    priceCents: int = Field(ge=1)
    imageUrl: str = ""
    status: str = "on"
    initialStock: int = Field(default=0, ge=0)


class ProductPatch(BaseModel):
    categoryId: int | None = None
    name: str | None = None
    spec: str | None = None
    description: str | None = None
    priceCents: int | None = Field(default=None, ge=1)
    imageUrl: str | None = None
    status: str | None = None


class ProductQuery(BaseModel):
    ids: list[int]


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def category_name(db: Session, category_id: int) -> str:
    category = db.get(Category, category_id)
    return category.name if category else ""


def product_out(db: Session, product: Product) -> dict:
    return {
        "id": product.id,
        "categoryId": product.category_id,
        "categoryName": category_name(db, product.category_id),
        "name": product.name,
        "spec": product.spec,
        "description": product.description,
        "priceCents": product.price_cents,
        "imageUrl": product.image_url,
        "status": product.status,
    }


def ensure_status(status: str) -> str:
    if status not in ("on", "off"):
        raise ApiError(400, "INVALID_STATUS", "商品状态只能是上架或下架")
    return status


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "catalog"}


@app.get("/catalog/categories")
def categories(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(Category).order_by(Category.sort_order, Category.id)).all()
    return {"items": [{"id": row.id, "name": row.name} for row in rows]}


@app.get("/catalog/products")
def products(
    categoryId: int | None = None,
    q: str | None = None,
    page: int = 1,
    pageSize: int = 12,
    db: Session = Depends(get_db),
) -> dict:
    page = max(page, 1)
    pageSize = min(max(pageSize, 1), 50)
    query = select(Product).where(Product.status == "on")
    count = select(func.count()).select_from(Product).where(Product.status == "on")
    if categoryId:
        query = query.where(Product.category_id == categoryId)
        count = count.where(Product.category_id == categoryId)
    if q:
        like = f"%{q.strip()}%"
        query = query.where(or_(Product.name.like(like), Product.spec.like(like)))
        count = count.where(or_(Product.name.like(like), Product.spec.like(like)))
    total = db.scalar(count) or 0
    rows = db.scalars(query.order_by(Product.id.desc()).offset((page - 1) * pageSize).limit(pageSize)).all()
    return {"items": [product_out(db, row) for row in rows], "page": page, "pageSize": pageSize, "total": total}


@app.get("/catalog/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = db.get(Product, product_id)
    if product is None or product.status != "on":
        raise ApiError(404, "PRODUCT_NOT_FOUND", "商品不存在或已下架")
    return product_out(db, product)


@app.post("/internal/products/query")
def query_products(body: ProductQuery, request: Request, db: Session = Depends(get_db)) -> dict:
    require_internal(request)
    if not body.ids:
        return {"items": []}
    rows = db.scalars(select(Product).where(Product.id.in_(body.ids))).all()
    return {"items": [product_out(db, row) for row in rows]}


@app.get("/admin/products")
def admin_products(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    rows = db.scalars(select(Product).order_by(Product.id.desc())).all()
    return {"items": [product_out(db, row) for row in rows]}


@app.post("/admin/products", status_code=201)
def create_product(body: ProductIn, request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    ensure_status(body.status)
    if db.get(Category, body.categoryId) is None:
        raise ApiError(400, "CATEGORY_NOT_FOUND", "分类不存在")
    moment = now()
    product = Product(
        category_id=body.categoryId,
        name=body.name.strip(),
        spec=body.spec.strip(),
        description=body.description.strip(),
        price_cents=body.priceCents,
        image_url=body.imageUrl.strip(),
        status=body.status,
        created_at=moment,
        updated_at=moment,
    )
    db.add(product)
    db.commit()
    try:
        response = httpx.post(
            setting("INVENTORY_URL", "http://127.0.0.1:8093") + "/internal/items",
            json={"productId": product.id, "available": body.initialStock},
            headers={
                "x-internal-token": setting("INTERNAL_TOKEN", "dev-internal-token"),
                "x-request-id": request.state.trace_id,
            },
            timeout=3.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ApiError(503, "INVENTORY_UNAVAILABLE", "商品已保存，但库存初始化失败") from exc
    return product_out(db, product)


@app.patch("/admin/products/{product_id}")
def update_product(product_id: int, body: ProductPatch, request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    product = db.get(Product, product_id)
    if product is None:
        raise ApiError(404, "PRODUCT_NOT_FOUND", "商品不存在")
    if body.categoryId is not None:
        if db.get(Category, body.categoryId) is None:
            raise ApiError(400, "CATEGORY_NOT_FOUND", "分类不存在")
        product.category_id = body.categoryId
    if body.name is not None:
        product.name = body.name.strip()
    if body.spec is not None:
        product.spec = body.spec.strip()
    if body.description is not None:
        product.description = body.description.strip()
    if body.priceCents is not None:
        product.price_cents = body.priceCents
    if body.imageUrl is not None:
        product.image_url = body.imageUrl.strip()
    if body.status is not None:
        product.status = ensure_status(body.status)
    product.updated_at = now()
    db.commit()
    return product_out(db, product)


@app.get("/admin/metrics")
def metrics(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin(request)
    total = db.scalar(select(func.count()).select_from(Product)) or 0
    on_shelf = db.scalar(select(func.count()).select_from(Product).where(Product.status == "on")) or 0
    return {"productCount": total, "onShelfCount": on_shelf}
