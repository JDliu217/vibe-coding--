"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ProductCard } from "../../components/ProductCard";
import { api } from "../../lib/api";
import { Category, Product } from "../../lib/types";
import { Suspense } from "react";

function ProductBrowser() {
  const params = useSearchParams();
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [categoryId, setCategoryId] = useState(params.get("categoryId") || "");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = (nextCategory = categoryId, nextQuery = q) => {
    setLoading(true);
    const search = new URLSearchParams({ pageSize: "24" });
    if (nextCategory) search.set("categoryId", nextCategory);
    if (nextQuery.trim()) search.set("q", nextQuery.trim());
    api<{ items: Product[] }>(`/api/catalog/products?${search.toString()}`)
      .then((data) => setProducts(data.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    api<{ items: Category[] }>("/api/catalog/categories")
      .then((data) => setCategories(data.items))
      .catch((err: Error) => setError(err.message));
    load(params.get("categoryId") || "", "");
  }, [params]);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">选购</h1>
      <form className="flex flex-col gap-2 sm:flex-row" onSubmit={(event) => { event.preventDefault(); load(); }}>
        <select className="rounded-xl border px-3 py-2" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
          <option value="">全部分类</option>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
        <input className="flex-1 rounded-xl border px-3 py-2" placeholder="搜索名称或规格" value={q} onChange={(event) => setQ(event.target.value)} />
        <button className="rounded-xl bg-leaf px-4 py-2 text-white" type="submit">搜索</button>
      </form>
      {loading && <p>正在加载商品...</p>}
      {error && <p className="text-red-700">{error}</p>}
      {!loading && !error && products.length === 0 && <p>没有符合条件的商品。</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {products.map((product) => <ProductCard key={product.id} product={product} />)}
      </div>
    </div>
  );
}

export default function ProductsPage() {
  return <Suspense fallback={<p>正在加载商品...</p>}><ProductBrowser /></Suspense>;
}
