"use client";

import { useEffect, useState } from "react";
import { addToCart } from "../../../lib/cart";
import { api, yuan } from "../../../lib/api";
import { Product } from "../../../lib/types";

export default function ProductDetail({ params }: { params: { id: string } }) {
  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [broken, setBroken] = useState(false);

  useEffect(() => {
    api<Product>(`/api/catalog/products/${params.id}`)
      .then(setProduct)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <p>正在加载商品...</p>;
  if (error) return <p className="text-red-700">{error}</p>;
  if (!product) return <p>没有找到商品。</p>;
  const stock = product.availableQuantity ?? 0;

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {product.imageUrl && !broken ? (
        <img alt={product.name} className="h-80 w-full rounded-3xl object-cover" src={product.imageUrl} onError={() => setBroken(true)} />
      ) : (
        <div className="flex h-80 items-center justify-center rounded-3xl bg-emerald-50 text-leaf">{product.categoryName}</div>
      )}
      <div className="space-y-4">
        <p className="text-sm text-emerald-700">{product.categoryName}</p>
        <h1 className="text-3xl font-bold">{product.name}</h1>
        <p className="text-stone-600">{product.spec}</p>
        <p>{product.description}</p>
        <p className="text-2xl font-bold text-leaf">{yuan(product.priceCents)}</p>
        <p>可售库存 {stock}</p>
        <label className="block text-sm">数量
          <input className="mt-1 w-24 rounded-xl border px-3 py-2" min={1} max={99} type="number" value={quantity} onChange={(event) => setQuantity(Number(event.target.value))} />
        </label>
        <button
          className="rounded-xl bg-leaf px-5 py-3 text-white disabled:bg-stone-300"
          disabled={stock < 1}
          type="button"
          onClick={() => {
            addToCart({
              productId: product.id,
              name: product.name,
              spec: product.spec,
              priceCents: product.priceCents,
              imageUrl: product.imageUrl,
            }, quantity);
            setNote("已加入购物车");
          }}
        >
          加入购物车
        </button>
        {note && <p className="text-leaf">{note}</p>}
      </div>
    </div>
  );
}
