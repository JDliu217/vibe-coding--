"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, yuan } from "../../../lib/api";
import { ShopOrder } from "../../../lib/types";

const STATUS: Record<string, string> = {
  creating: "创建中",
  created: "已创建",
  completed: "已完成",
  cancelled: "已取消",
  failed: "创建失败",
};

export default function AdminOrders() {
  const [status, setStatus] = useState("");
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = (next = status) => {
    setLoading(true);
    const query = next ? `?status=${next}` : "";
    api<{ items: ShopOrder[] }>(`/api/admin/orders${query}`)
      .then((data) => setOrders(data.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(""); }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">订单管理</h1>
      <select className="rounded-xl border px-3 py-2" value={status} onChange={(event) => { setStatus(event.target.value); load(event.target.value); }}>
        <option value="">全部状态</option>
        {Object.entries(STATUS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>
      {loading && <p>正在加载订单...</p>}
      {error && <p className="text-red-700">{error}</p>}
      {!loading && orders.length === 0 && <p>没有订单。</p>}
      <div className="overflow-x-auto rounded-2xl bg-white">
        <table className="w-full text-left text-sm">
          <thead><tr className="border-b"><th className="p-3">单号</th><th>用户</th><th>金额</th><th>状态</th></tr></thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id} className="border-b">
                <td className="p-3"><Link href={`/orders/${order.id}`}>#{order.id}</Link></td>
                <td>{order.userId}</td>
                <td>{yuan(order.totalCents)}</td>
                <td>{STATUS[order.status] || order.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
