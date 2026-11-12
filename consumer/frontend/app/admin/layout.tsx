"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("freshmart-user");
    const user = raw ? JSON.parse(raw) : null;
    if (!user || user.role !== "admin") {
      router.replace("/forbidden");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) return <p>正在确认权限...</p>;
  return (
    <div className="space-y-4">
      <nav className="flex flex-wrap gap-3 text-sm">
        <Link href="/admin">概览</Link>
        <Link href="/admin/products">商品</Link>
        <Link href="/admin/inventory">库存</Link>
        <Link href="/admin/orders">订单</Link>
      </nav>
      {children}
    </div>
  );
}
