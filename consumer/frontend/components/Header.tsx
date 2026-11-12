"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { cartCount } from "../lib/cart";
import { User } from "../lib/types";

export function Header() {
  const [count, setCount] = useState(0);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const sync = () => {
      setCount(cartCount());
      const raw = localStorage.getItem("freshmart-user");
      setUser(raw ? JSON.parse(raw) : null);
    };
    sync();
    window.addEventListener("freshmart-cart", sync);
    window.addEventListener("freshmart-auth", sync);
    return () => {
      window.removeEventListener("freshmart-cart", sync);
      window.removeEventListener("freshmart-auth", sync);
    };
  }, []);

  const logout = () => {
    localStorage.removeItem("freshmart-token");
    localStorage.removeItem("freshmart-user");
    localStorage.removeItem("freshmart-user-id");
    window.dispatchEvent(new Event("freshmart-auth"));
    window.dispatchEvent(new Event("freshmart-cart"));
  };

  return (
    <header className="sticky top-0 z-10 border-b border-emerald-100 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="text-xl font-bold tracking-wide text-leaf">鲜拾</Link>
        <nav className="flex flex-wrap items-center gap-3 text-sm">
          <Link href="/products">选购</Link>
          <Link href="/cart">购物车{count ? ` (${count})` : ""}</Link>
          <Link href="/orders">订单</Link>
          {user?.role === "admin" && <Link href="/admin">管理</Link>}
          {user ? (
            <button className="text-leaf" onClick={logout} type="button">退出</button>
          ) : (
            <Link className="rounded-full bg-leaf px-3 py-1 text-white" href="/login">登录</Link>
          )}
        </nav>
      </div>
    </header>
  );
}
