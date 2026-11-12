"use client";

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

export default function OrderDetail({ params }: { params: { id: string } }) {
  const [order, setOrder] = useState<ShopOrder | null>(null);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState("");

  const load = () => {
    api<ShopOrder>(`/api/orders/${params.id}`)
      .then(setOrder)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [params.id]);

  const act = async (action: "complete" | "cancel") => {
    setPending(action);
    setError("");
    try {
      const next = await api<ShopOrder>(`/api/orders/${params.id}/${action}`, { method: "POST" });
      setOrder(next);
      setNote(action === "complete" ? "订单已完成" : "订单已取消");
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setPending("");
    }
  };

  if (loading) return <p>正在加载订单...</p>;
  if (!order) return <p className="text-red-700">{error || "没有找到订单"}</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">订单 #{order.id}</h1>
      <p>状态：{STATUS[order.status] || order.status}</p>
      <p>下单时间：{order.createdAt}</p>
      <p className="text-sm text-stone-500">追踪号 {order.traceId}</p>
      <div className="space-y-2">
        {order.items.map((item) => (
          <div key={item.productId} className="rounded-2xl bg-white p-4">
            <strong>{item.productName}</strong>
            <p className="text-sm text-stone-500">{item.spec} · {yuan(item.unitPriceCents)} × {item.quantity}</p>
          </div>
        ))}
      </div>
      <p className="text-xl font-bold">合计 {yuan(order.totalCents)}</p>
      {order.status === "created" && (
        <div className="flex gap-2">
          <button className="rounded-xl bg-leaf px-4 py-2 text-white disabled:bg-stone-300" disabled={!!pending} type="button" onClick={() => act("complete")}>{pending === "complete" ? "处理中" : "确认完成"}</button>
          <button className="rounded-xl border px-4 py-2 disabled:bg-stone-100" disabled={!!pending} type="button" onClick={() => act("cancel")}>{pending === "cancel" ? "处理中" : "取消订单"}</button>
        </div>
      )}
      {note && <p className="text-leaf">{note}</p>}
      {error && <p className="text-red-700">{error}</p>}
    </div>
  );
}
