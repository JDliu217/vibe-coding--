"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { readCart, writeCart } from "../../lib/cart";
import { api, yuan } from "../../lib/api";
import { CartLine, ShopOrder } from "../../lib/types";

export default function CartPage() {
  const router = useRouter();
  const [lines, setLines] = useState<CartLine[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => setLines(readCart()), []);

  const update = (productId: number, quantity: number) => {
    const next = lines
      .map((line) => (line.productId === productId ? { ...line, quantity } : line))
      .filter((line) => line.quantity > 0);
    setLines(next);
    writeCart(next);
  };

  const checkout = async () => {
    if (!localStorage.getItem("freshmart-token")) {
      router.push("/login?next=/cart");
      return;
    }
    setSubmitting(true);
    setError("");
    const fingerprint = JSON.stringify(lines.map((line) => [line.productId, line.quantity]));
    const saved = sessionStorage.getItem("freshmart-checkout");
    const parsed = saved ? JSON.parse(saved) : null;
    const key = parsed?.fingerprint === fingerprint ? parsed.key : crypto.randomUUID();
    sessionStorage.setItem("freshmart-checkout", JSON.stringify({ fingerprint, key }));
    try {
      const order = await api<ShopOrder>("/api/orders", {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify({ items: lines.map((line) => ({ productId: line.productId, quantity: line.quantity })) }),
      });
      writeCart([]);
      setLines([]);
      sessionStorage.removeItem("freshmart-checkout");
      router.push(`/orders/${order.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "下单失败");
    } finally {
      setSubmitting(false);
    }
  };

  const total = lines.reduce((sum, line) => sum + line.priceCents * line.quantity, 0);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">购物车</h1>
      {lines.length === 0 && <p>购物车是空的。<Link className="text-leaf" href="/products">去选购</Link></p>}
      {lines.map((line) => (
        <div key={line.productId} className="flex flex-col gap-3 rounded-2xl bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <strong>{line.name}</strong>
            <p className="text-sm text-stone-500">{line.spec} · {yuan(line.priceCents)}</p>
          </div>
          <div className="flex items-center gap-2">
            <input className="w-20 rounded-xl border px-2 py-1" min={1} max={99} type="number" value={line.quantity} onChange={(event) => update(line.productId, Number(event.target.value))} />
            <button className="text-red-700" type="button" onClick={() => update(line.productId, 0)}>删除</button>
          </div>
        </div>
      ))}
      {lines.length > 0 && (
        <div className="rounded-2xl bg-white p-4">
          <p className="text-lg font-bold">合计 {yuan(total)}</p>
          <p className="text-sm text-stone-500">最终金额由服务器按当前商品价格计算。</p>
          <button className="mt-3 rounded-xl bg-leaf px-5 py-3 text-white disabled:bg-stone-300" disabled={submitting} type="button" onClick={checkout}>
            {submitting ? "正在提交" : "提交订单"}
          </button>
          {error && <p className="mt-2 text-red-700">{error}</p>}
        </div>
      )}
    </div>
  );
}
