"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

type Customer = {
  id: number;
  name: string | null;
  phone: string | null;
  query_text: string;
  locality: string | null;
  bhk: string | null;
  budget: number | null;
  source: string;
  source_chat: string;
  enquiry_date: string | null;
};

export default function Customers() {
  const [rows, setRows] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [locality, setLocality] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search.trim()) params.set("name", search.trim());
    if (locality.trim()) params.set("locality", locality.trim());
    try {
      const res = await api(`/api/customers?${params}`);
      if (!res.ok) {
        setError(res.status === 401 ? "Session expired — sign in again." : `Failed (${res.status}).`);
        return;
      }
      setError("");
      setRows((await res.json()) as Customer[]);
    } catch {
      setError("Could not reach the API. Is it running?");
    } finally {
      setLoading(false);
    }
  }, [search, locality]);

  useEffect(() => {
    const timer = setTimeout(load, 250);
    return () => clearTimeout(timer);
  }, [load]);

  return (
    <>
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-neutral-200 bg-white px-4 md:h-16">
        <h1 className="font-semibold">Customers</h1>
        <span className="text-sm text-neutral-500">
          {loading ? "loading…" : `${rows.length} ${rows.length === 1 ? "person" : "people"}`}
        </span>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="flex flex-wrap gap-2 border-b border-neutral-200 bg-white px-4 py-3">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search name…"
            className="min-w-0 flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-[#075E54]"
          />
          <input
            value={locality}
            onChange={(event) => setLocality(event.target.value)}
            placeholder="Locality (e.g. Andheri)"
            className="min-w-0 flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-[#075E54]"
          />
        </div>

        {error ? <p className="px-4 py-3 text-sm text-red-600">{error}</p> : null}

        {!loading && !error && rows.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-neutral-500">
            No customers yet. Attach a WhatsApp ZIP in the chat.
          </p>
        ) : null}

        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-neutral-50 text-xs uppercase tracking-wide text-neutral-500">
              <tr>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Contact</th>
                <th className="px-4 py-3 font-medium">Query</th>
                <th className="px-4 py-3 font-medium">Locality</th>
                <th className="px-4 py-3 font-medium">BHK</th>
                <th className="px-4 py-3 font-medium">Budget</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {rows.map((row) => (
                <tr key={row.id} className="align-top hover:bg-neutral-50">
                  <td className="px-4 py-3 font-medium">{row.name ?? "—"}</td>
                  <td className="px-4 py-3">
                    {row.phone ? (
                      <span className="whitespace-nowrap">{row.phone}</span>
                    ) : (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                        phone missing
                      </span>
                    )}
                  </td>
                  <td className="max-w-[280px] px-4 py-3 text-neutral-600">
                    <span className="line-clamp-2" title={row.query_text}>
                      {row.query_text}
                    </span>
                  </td>
                  <td className="px-4 py-3">{row.locality ?? "—"}</td>
                  <td className="px-4 py-3">{row.bhk ?? "—"}</td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {row.budget ? `₹${row.budget.toLocaleString("en-IN")}` : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs">
                      {row.source.startsWith("audio") ? "voice" : "text"}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-neutral-500">
                    {row.enquiry_date ? new Date(row.enquiry_date).toLocaleDateString("en-IN") : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
