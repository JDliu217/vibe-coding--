import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "common"))

from sqlalchemy import select

from common.db import SessionLocal, ensure_database
from common.models import Category, InventoryItem, Product, User
from common.security import hash_password

CATEGORIES = ["时令蔬菜", "新鲜水果", "肉禽蛋品", "海鲜水产"]
PRODUCTS = [
    ("时令蔬菜", "有机菠菜", "300g", "当天到店的嫩叶菠菜", 690, "https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=800&q=60", 40),
    ("时令蔬菜", "樱桃番茄", "500g", "酸甜小番茄，适合凉拌", 1290, "https://images.unsplash.com/photo-1546470427-227c7369a9b5?auto=format&fit=crop&w=800&q=60", 36),
    ("时令蔬菜", "水果黄瓜", "500g", "水分足，可直接生吃", 490, "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?auto=format&fit=crop&w=800&q=60", 30),
    ("时令蔬菜", "西兰花", "约400g", "一颗装，花球紧实", 890, "https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?auto=format&fit=crop&w=800&q=60", 24),
    ("新鲜水果", "红富士苹果", "1kg", "脆甜，家庭装", 1590, "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=800&q=60", 28),
    ("新鲜水果", "香蕉", "1kg", "自然熟，适合早餐", 990, "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=800&q=60", 32),
    ("新鲜水果", "赣南脐橙", "1kg", "汁水多，果皮好剥", 1890, "https://images.unsplash.com/photo-1547514701-42782101795e?auto=format&fit=crop&w=800&q=60", 22),
    ("肉禽蛋品", "土鸡蛋", "10枚", "当日分装", 1690, "https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=800&q=60", 26),
    ("肉禽蛋品", "鲜牛奶", "1L", "冷藏巴氏奶", 1290, "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=800&q=60", 18),
    ("肉禽蛋品", "鸡胸肉", "400g", "冷鲜去皮", 2190, "https://images.unsplash.com/photo-1604503468506-a8da13d82791?auto=format&fit=crop&w=800&q=60", 16),
    ("海鲜水产", "基围虾", "300g", "冰鲜，适合白灼", 3990, "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?auto=format&fit=crop&w=800&q=60", 12),
    ("海鲜水产", "三文鱼柳", "200g", "冷鲜切片", 4990, "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=800&q=60", 8),
]
USERS = [
    ("13800000000", "Admin123456", "admin", "店长"),
    ("13900001001", "User123456", "user", "林夏"),
]


def moment() -> datetime:
    return datetime.now().replace(microsecond=0)


def main() -> None:
    ensure_database()
    session = SessionLocal()
    current = moment()
    categories = {}
    for index, name in enumerate(CATEGORIES, start=1):
        row = session.scalar(select(Category).where(Category.name == name))
        if row is None:
            row = Category(name=name, sort_order=index)
            session.add(row)
            session.flush()
        categories[name] = row
    for category_name, name, spec, description, price, image, stock in PRODUCTS:
        product = session.scalar(select(Product).where(Product.name == name))
        if product is None:
            product = Product(
                category_id=categories[category_name].id,
                name=name,
                spec=spec,
                description=description,
                price_cents=price,
                image_url=image,
                status="on",
                created_at=current,
                updated_at=current,
            )
            session.add(product)
            session.flush()
        inventory = session.scalar(select(InventoryItem).where(InventoryItem.product_id == product.id))
        if inventory is None:
            session.add(
                InventoryItem(
                    product_id=product.id,
                    available_quantity=stock,
                    reserved_quantity=0,
                    updated_at=current,
                )
            )
    for phone, password, role, nickname in USERS:
        user = session.scalar(select(User).where(User.phone == phone))
        if user is None:
            session.add(
                User(
                    phone=phone,
                    nickname=nickname,
                    password_hash=hash_password(password),
                    role=role,
                    created_at=current,
                    updated_at=current,
                )
            )
        else:
            user.role = role
            user.nickname = nickname
            user.password_hash = hash_password(password)
            user.updated_at = current
    session.commit()
    session.close()
    print("seeded")


if __name__ == "__main__":
    main()
