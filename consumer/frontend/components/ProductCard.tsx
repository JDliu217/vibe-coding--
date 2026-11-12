"use client";

import Link from "next/link";
import { useState } from "react";
import { addToCart } from "../lib/cart";
import { yuan } from "../lib/api";
import { Product } from "../lib/types";

export function ProductCard({ product }: { product: Product }) {
  const [note, setNote] = useState("");
  const [broken, setBroken] = useState(false);
  const stock = product.availableQuantity ?? 0;
  return (
    <article className="overflow-hidden rounded-2xl border border-emerald-100 bg-white">
      <Link href={`/products/${product.id}`}>
        {product.imageUrl && !broken ? (
          <img alt={product.name} className="h-40 w-full object-cover" src={product.imageUrl} onError={() => setBroken(true)} />
        ) : (
          <div className="flex h-40 items-center justify-center bg-emerald-50 text-leaf">{product.categoryName}</div>
        )}
      </Link>
      <div className="space-y-2 p-4">
        <p className="text-xs text-emerald-700">{product.categoryName}</p>
        <Link href={`/products/${product.id}`} className="block font-semibold">{product.name}</Link>
        <p className="text-sm text-stone-500">{product.spec}</p>
        <div className="flex items-center justify-between">
          <strong>{yuan(product.priceCents)}</strong>
          <span className="text-xs text-stone-500">库存 {stock}</span>
        </div>
        <button
          className="w-full rounded-xl bg-leaf py-2 text-sm text-white disabled:bg-stone-300"
          disabled={stock < 1 || product.status !== "on"}
          type="button"
          onClick={() => {
            addToCart({
              productId: product.id,
              name: product.name,
              spec: product.spec,
              priceCents: product.priceCents,
              imageUrl: product.imageUrl,
            }, 1);
            setNote("已加入购物车");
          }}
        >
          加入购物车
        </button>
        {note && <p className="text-xs text-leaf">{note}</p>}
      </div>
    </article>
  );
}
