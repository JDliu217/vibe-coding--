"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "../../lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      await api("/api/auth/register", { method: "POST", body: JSON.stringify({ phone, password, nickname }) });
      router.push("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    } finally {
      setPending(false);
    }
  };

  return (
    <form className="mx-auto max-w-md space-y-3 rounded-3xl bg-white p-6" onSubmit={submit}>
      <h1 className="text-2xl font-bold">注册</h1>
      <input className="w-full rounded-xl border px-3 py-2" placeholder="手机号" value={phone} onChange={(event) => setPhone(event.target.value)} />
      <input className="w-full rounded-xl border px-3 py-2" placeholder="昵称，可选" value={nickname} onChange={(event) => setNickname(event.target.value)} />
      <input className="w-full rounded-xl border px-3 py-2" placeholder="密码至少 6 位" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
      <button className="w-full rounded-xl bg-leaf py-2 text-white disabled:bg-stone-300" disabled={pending} type="submit">{pending ? "正在注册" : "注册"}</button>
      {error && <p className="text-red-700">{error}</p>}
    </form>
  );
}
