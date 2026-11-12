"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ProductCard } from "../components/ProductCard";
import { api } from "../lib/api";
import { Category, Product } from "../lib/types";

export default function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api<{ items: Category[] }>("/api/catalog/categories"),
      api<{ items: Product[] }>("/api/catalog/products?pageSize=8"),
    ])
      .then(([categoryData, productData]) => {
        setCategories(categoryData.items);
        setProducts(productData.items);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-gradient-to-br from-emerald-700 to-lime-600 px-6 py-10 text-white">
        <p className="text-sm text-emerald-100">今日鲜到</p>
        <h1 className="mt-2 text-4xl font-bold">把当季食材买回家</h1>
        <p className="mt-3 max-w-xl text-emerald-50">蔬菜、水果、肉禽和海鲜。先挑选，再下单。这里没有优惠券和促销价。</p>
        <Link className="mt-6 inline-block rounded-full bg-white px-5 py-2 font-semibold text-leaf" href="/products">开始选购</Link>
      </section>
      <section className="flex flex-wrap gap-2">
        {categories.map((category) => (
          <Link key={category.id} className="rounded-full bg-white px-4 py-2 text-sm shadow-sm" href={`/products?categoryId=${category.id}`}>
            {category.name}
          </Link>
        ))}
      </section>
      {loading && <p>正在加载商品...</p>}
      {error && <p className="text-red-700">{error}</p>}
      {!loading && !error && products.length === 0 && <p>暂时没有在售商品。</p>}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {products.map((product) => <ProductCard key={product.id} product={product} />)}
      </section>
    </div>
  );
}
