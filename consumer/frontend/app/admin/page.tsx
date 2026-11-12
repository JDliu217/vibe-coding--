"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Overview = {
  catalog: { productCount: number; onShelfCount: number };
  inventory: { lowStockCount: number; threshold: number };
  orders: { orderCount: number; byStatus: Record<string, number> };
};

export default function AdminHome() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Overview>("/api/admin/overview")
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>正在加载经营数据...</p>;
  if (error) return <p className="text-red-700">{error}</p>;
  if (!data) return <p>没有数据。</p>;
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <article className="rounded-2xl bg-white p-4"><p>商品数</p><strong className="text-3xl">{data.catalog.productCount}</strong><p className="text-sm">在售 {data.catalog.onShelfCount}</p></article>
      <article className="rounded-2xl bg-white p-4"><p>订单数</p><strong className="text-3xl">{data.orders.orderCount}</strong><p className="text-sm">已创建 {data.orders.byStatus.created || 0} / 已完成 {data.orders.byStatus.completed || 0}</p></article>
      <article className="rounded-2xl bg-white p-4"><p>库存预警</p><strong className="text-3xl">{data.inventory.lowStockCount}</strong><p className="text-sm">可用库存不超过 {data.inventory.threshold}</p></article>
    </div>
  );
}
