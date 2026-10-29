"use client";

import { useEffect, useRef, useState } from "react";

type Msg = { from: "me" | "bot"; text: string };

// shortcut: canned answers, no LLM behind them — ceiling: replies never change.
// Upgrade: POST /api/chat to the FastAPI agent and append the streamed reply.
const GREETING: Msg = {
  from: "bot",
  text: "Hi! I'm your BrokerDesk assistant. Once your WhatsApp Business account is connected, ask me anything about your rentals, appointments or brokerage.",
};

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>([GREETING]);
  const [value, setValue] = useState("");
  const [pending, setPending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [msgs]);

  async function send(event: React.FormEvent) {
    event.preventDefault();
    const text = value.trim();
    if (!text || pending) return;

    const history = [...msgs, { from: "me" as const, text }].slice(-10);
    setMsgs((m) => [...m, { from: "me", text }]);
    setValue("");
    setPending(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: history.map((m) => ({
            role: m.from === "me" ? "user" : "assistant",
            content: m.text,
          })),
        }),
      });

      if (!res.ok) {
        const detail =
          res.status === 401
            ? "Session expired — reload and sign in again."
            : `Request failed (${res.status}).`;
        setMsgs((m) => [...m, { from: "bot", text: detail }]);
        return;
      }

      const data = (await res.json()) as { reply: string };
      setMsgs((m) => [...m, { from: "bot", text: data.reply }]);
    } catch {
      setMsgs((m) => [
        ...m,
        { from: "bot", text: "Could not reach the server. Is the API running on port 8000?" },
      ]);
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-neutral-200 bg-white px-4 md:h-16">
        <h1 className="font-semibold">Assistant</h1>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
          Not connected yet
        </span>
      </header>

      <div ref={listRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-5">
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.from === "me" ? "justify-end" : "justify-start"}`}>
            <p
              className={`max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm shadow-sm sm:max-w-[70%] ${
                m.from === "me"
                  ? "rounded-tr-sm bg-[#25D366] text-white"
                  : "rounded-tl-sm bg-white text-neutral-800 ring-1 ring-neutral-200"
              }`}
            >
              {m.text}
            </p>
          </div>
        ))}
        {pending && msgs[msgs.length - 1]?.from === "me" ? (
          <p className="text-sm text-neutral-400">typing…</p>
        ) : null}
      </div>

      <form
        onSubmit={send}
        className="flex shrink-0 gap-2 border-t border-neutral-200 bg-white p-3"
      >
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask about rentals, appointments or brokerage…"
          enterKeyHint="send"
          autoComplete="off"
          className="min-w-0 flex-1 rounded-full border border-neutral-300 px-4 py-2.5 text-base outline-none focus:border-[#075E54] focus:ring-2 focus:ring-[#075E54]/20"
        />
        <button
          type="submit"
          disabled={!value.trim() || pending}
          className="shrink-0 rounded-full bg-[#075E54] px-5 text-sm font-semibold text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </>
  );
}
