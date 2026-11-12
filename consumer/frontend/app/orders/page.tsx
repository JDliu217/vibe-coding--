"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, yuan } from "../../lib/api";
import { ShopOrder } from "../../lib/types";

const STATUS: Record<string, string> = {
  creating: "创建中",
  created: "已创建",
  completed: "已完成",
  cancelled: "已取消",
  failed: "创建失败",
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("freshmart-token")) {
      setError("请先登录后查看订单");
      setLoading(false);
      return;
    }
    api<{ items: ShopOrder[] }>("/api/orders/my")
      .then((data) => setOrders(data.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">我的订单</h1>
      {loading && <p>正在加载订单...</p>}
      {error && <p className="text-red-700">{error}</p>}
      {!loading && !error && orders.length === 0 && <p>还没有订单。</p>}
      {orders.map((order) => (
        <Link key={order.id} href={`/orders/${order.id}`} className="block rounded-2xl bg-white p-4">
          <div className="flex items-center justify-between">
            <strong>订单 #{order.id}</strong>
            <span>{STATUS[order.status] || order.status}</span>
          </div>
          <p className="text-sm text-stone-500">{order.createdAt} · {yuan(order.totalCents)}</p>
        </Link>
      ))}
    </div>
  );
}
