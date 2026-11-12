"use client";

import { useEffect, useState } from "react";
import { api } from "../../../lib/api";
import { Product } from "../../../lib/types";

type Stock = { productId: number; availableQuantity: number; reservedQuantity: number };
type Adjustment = { id: number; productId: number; availableBefore: number; availableAfter: number; reason: string; createdAt: string };

export default function AdminInventory() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [products, setProducts] = useState<Record<number, Product>>({});
  const [logs, setLogs] = useState<Adjustment[]>([]);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [error, setError] = useState("");
  const [note, setNote] = useState("");

  const load = () => {
    Promise.all([
      api<{ items: Stock[] }>("/api/admin/inventory"),
      api<{ items: Product[] }>("/api/admin/products"),
      api<{ items: Adjustment[] }>("/api/admin/inventory/adjustments"),
    ]).then(([stockData, productData, logData]) => {
      setStocks(stockData.items);
      setProducts(Object.fromEntries(productData.items.map((product) => [product.id, product])));
      setLogs(logData.items);
    }).catch((err: Error) => setError(err.message));
  };

  useEffect(load, []);

  const save = async (row: Stock) => {
    setError("");
    try {
      await api(`/api/inventory/${row.productId}`, {
        method: "PATCH",
        body: JSON.stringify({ availableQuantity: Number(drafts[row.productId] ?? row.availableQuantity), reason: "后台调整可用库存" }),
      });
      setNote("库存已更新");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "调整失败");
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">库存</h1>
      {note && <p className="text-leaf">{note}</p>}
      {error && <p className="text-red-700">{error}</p>}
      <div className="overflow-x-auto rounded-2xl bg-white">
        <table className="w-full text-left text-sm">
          <thead><tr className="border-b"><th className="p-3">商品</th><th>可用</th><th>预占</th><th>调整为</th></tr></thead>
          <tbody>
            {stocks.map((row) => (
              <tr key={row.productId} className="border-b">
                <td className="p-3">{products[row.productId]?.name || row.productId}</td>
                <td>{row.availableQuantity}</td>
                <td>{row.reservedQuantity}</td>
                <td className="p-3">
                  <input className="w-20 rounded border px-2 py-1" value={drafts[row.productId] ?? String(row.availableQuantity)} onChange={(event) => setDrafts({ ...drafts, [row.productId]: event.target.value })} />
                  <button className="ml-2 text-leaf" type="button" onClick={() => save(row)}>保存</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 className="font-semibold">调整记录</h2>
      {logs.length === 0 && <p>还没有调整记录。</p>}
      {logs.map((log) => (
        <p key={log.id} className="text-sm">{log.createdAt} · 商品 {products[log.productId]?.name || log.productId} · {log.availableBefore} → {log.availableAfter} · {log.reason}</p>
      ))}
    </div>
  );
}
