"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, yuan } from "../../../lib/api";
import { Category, Product } from "../../../lib/types";

export default function AdminProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [pending, setPending] = useState(false);
  const [form, setForm] = useState({ name: "", spec: "", price: "9.90", categoryId: "", stock: "10", description: "" });

  const load = () => {
    Promise.all([
      api<{ items: Product[] }>("/api/admin/products"),
      api<{ items: Category[] }>("/api/catalog/categories"),
    ]).then(([productData, categoryData]) => {
      setProducts(productData.items);
      setCategories(categoryData.items);
      if (!form.categoryId && categoryData.items[0]) setForm((current) => ({ ...current, categoryId: String(categoryData.items[0].id) }));
    }).catch((err: Error) => setError(err.message));
  };

  useEffect(load, []);

  const create = async (event: FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      await api("/api/admin/products", {
        method: "POST",
        body: JSON.stringify({
          name: form.name,
          spec: form.spec,
          description: form.description,
          categoryId: Number(form.categoryId),
          priceCents: Math.round(Number(form.price) * 100),
          initialStock: Number(form.stock),
          status: "on",
        }),
      });
      setNote("商品已上架");
      setForm({ ...form, name: "", spec: "", description: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setPending(false);
    }
  };

  const toggle = async (product: Product) => {
    setError("");
    try {
      await api(`/api/admin/products/${product.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: product.status === "on" ? "off" : "on" }),
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败");
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">商品管理</h1>
      <form className="grid gap-2 rounded-2xl bg-white p-4 md:grid-cols-3" onSubmit={create}>
        <input className="rounded-xl border px-3 py-2" placeholder="名称" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
        <input className="rounded-xl border px-3 py-2" placeholder="规格" value={form.spec} onChange={(event) => setForm({ ...form, spec: event.target.value })} required />
        <input className="rounded-xl border px-3 py-2" placeholder="价格（元）" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} required />
        <select className="rounded-xl border px-3 py-2" value={form.categoryId} onChange={(event) => setForm({ ...form, categoryId: event.target.value })}>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
        <input className="rounded-xl border px-3 py-2" placeholder="初始库存" value={form.stock} onChange={(event) => setForm({ ...form, stock: event.target.value })} required />
        <button className="rounded-xl bg-leaf text-white disabled:bg-stone-300" disabled={pending} type="submit">{pending ? "保存中" : "新增并上架"}</button>
      </form>
      {note && <p className="text-leaf">{note}</p>}
      {error && <p className="text-red-700">{error}</p>}
      <div className="overflow-x-auto rounded-2xl bg-white">
        <table className="w-full text-left text-sm">
          <thead><tr className="border-b"><th className="p-3">名称</th><th>价格</th><th>库存</th><th>状态</th><th></th></tr></thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id} className="border-b">
                <td className="p-3">{product.name}<div className="text-stone-500">{product.spec}</div></td>
                <td>{yuan(product.priceCents)}</td>
                <td>{product.availableQuantity ?? "-"}</td>
                <td>{product.status === "on" ? "在售" : "下架"}</td>
                <td><button type="button" onClick={() => toggle(product)}>{product.status === "on" ? "下架" : "上架"}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
