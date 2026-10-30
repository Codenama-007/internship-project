"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await api("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!res.ok) {
        setError("Wrong password. Try again.");
        setBusy(false);
        return;
      }
      router.replace("/app");
      router.refresh();
    } catch {
      setError("Cannot reach the server. Is the API running?");
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm"
      >
        <h1 className="text-2xl font-bold">
          Broker<span className="text-[#075E54]">Desk</span>
        </h1>
        <p className="mt-1 text-sm text-neutral-500">Broker login — one account, no signup.</p>

        <label htmlFor="password" className="mt-6 block text-sm font-medium">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoFocus
          className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 outline-none focus:border-[#075E54] focus:ring-2 focus:ring-[#075E54]/20"
        />

        {error ? (
          <p className="mt-3 text-sm font-medium text-red-600" role="alert">
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={busy}
          className="mt-5 w-full rounded-lg bg-[#075E54] px-4 py-2.5 font-semibold text-white transition hover:bg-[#05453f] disabled:opacity-60"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>

        <Link href="/" className="mt-4 block text-center text-sm text-neutral-500 hover:text-[#075E54]">
          ← Back to home
        </Link>
      </form>
    </main>
  );
}
