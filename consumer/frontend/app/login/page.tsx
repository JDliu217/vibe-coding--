"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { api } from "../../lib/api";
import { User } from "../../lib/types";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const data = await api<{ accessToken: string; user: User }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ phone, password }),
      });
      localStorage.setItem("freshmart-token", data.accessToken);
      localStorage.setItem("freshmart-user", JSON.stringify(data.user));
      localStorage.setItem("freshmart-user-id", String(data.user.id));
      window.dispatchEvent(new Event("freshmart-auth"));
      window.dispatchEvent(new Event("freshmart-cart"));
      router.push(params.get("next") || "/products");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setPending(false);
    }
  };

  return (
    <form className="mx-auto max-w-md space-y-3 rounded-3xl bg-white p-6" onSubmit={submit}>
      <h1 className="text-2xl font-bold">登录</h1>
      <input className="w-full rounded-xl border px-3 py-2" placeholder="手机号" value={phone} onChange={(event) => setPhone(event.target.value)} />
      <input className="w-full rounded-xl border px-3 py-2" placeholder="密码" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
      <button className="w-full rounded-xl bg-leaf py-2 text-white disabled:bg-stone-300" disabled={pending} type="submit">{pending ? "正在登录" : "登录"}</button>
      {error && <p className="text-red-700">{error}</p>}
      <Link className="block text-sm text-leaf" href="/register">没有账号，去注册</Link>
    </form>
  );
}

export default function LoginPage() {
  return <Suspense fallback={<p>正在打开登录...</p>}><LoginForm /></Suspense>;
}
