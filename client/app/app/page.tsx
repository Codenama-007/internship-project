"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

type Msg = { from: "me" | "bot"; text: string; href?: string };

const GREETING: Msg = {
  from: "bot",
  text: "Hi! Attach a WhatsApp export ZIP and I'll pull out the customers. Or just ask me something.",
};

const MAX_UPLOAD = 100 * 1024 * 1024;
const ZIP = /\.zip$/i;
const AUDIO = /\.(opus|ogg|m4a|mp3|wav|webm)$/i;

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>([GREETING]);
  const [value, setValue] = useState("");
  const [pending, setPending] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [msgs]);

  useEffect(() => () => {
    if (timerRef.current) clearInterval(timerRef.current);
  }, []);

  function add(msg: Msg) {
    setMsgs((m) => [...m, msg]);
  }

  function pick(selected: File | null) {
    if (!selected) return;
    if (selected.size > MAX_UPLOAD) {
      add({ from: "bot", text: "File 100 MB se badi hai. Chhoti file bhejo." });
      return;
    }
    if (!ZIP.test(selected.name) && !AUDIO.test(selected.name)) {
      add({ from: "bot", text: "Sirf .zip ya voice note (.opus/.ogg/.m4a/.mp3/.wav) bhej sakte ho." });
      return;
    }
    setFile(selected);
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setFile(new File([blob], `voice-${Date.now()}.webm`, { type: blob.type }));
      };
      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
      setSeconds(0);
      timerRef.current = window.setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch {
      add({ from: "bot", text: "Mic permission nahi mila. Browser settings me microphone allow karo." });
    }
  }

  function stopRecording() {
    recorderRef.current?.stop();
    recorderRef.current = null;
    setRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  async function uploadZip(zip: File, note: string) {
    const body = new FormData();
    body.append("file", zip);
    body.append(
      "language",
      /\b(the|and|please|show|list|my|all|how|what|customers)\b/i.test(note) ? "english" : "hinglish"
    );
    let res: Response;
    try {
      res = await fetch("/api/ingest/zip", { method: "POST", body });
    } catch {
      add({ from: "bot", text: "Upload fail hua: server se connect nahi ho paaya." });
      return;
    }
    if (!res.ok) {
      const detail = await res
        .json()
        .then((data: { detail?: string }) => data.detail)
        .catch(() => null);
      add({
        from: "bot",
        text:
          res.status === 401
            ? "Session expired — reload and sign in again."
            : `Upload fail hua (${res.status}): ${detail ?? "server error"}`,
      });
      return;
    }
    const data = (await res.json()) as { summary: string };
    add({ from: "bot", text: data.summary, href: "/app/customers" });
  }

  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (pending || recording) return;
    const text = value.trim();
    if (!text && !file) return;

    if (text) add({ from: "me", text });
    if (file) add({ from: "me", text: `📎 ${file.name} (${(file.size / 1024).toFixed(0)} KB)` });

    const attached = file;
    setValue("");
    setFile(null);
    setPending(true);

    try {
      if (attached && ZIP.test(attached.name)) {
        add({ from: "bot", text: "ZIP mila. Padh raha hoon — 2-3 minute lag sakte hain…" });
        await uploadZip(attached, text);
      } else if (attached) {
        add({
          from: "bot",
          text: "Voice note mila, transcribe karna baaki hai (step 5 me aayega).",
        });
      } else {
        const history = [...msgs, { from: "me" as const, text }].slice(-10);
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
          add({
            from: "bot",
            text: res.status === 401 ? "Session expired — reload and sign in again." : `Request failed (${res.status}).`,
          });
          return;
        }
        const data = (await res.json()) as { reply: string; href?: string };
        add({ from: "bot", text: data.reply, href: data.href });
      }
    } catch {
      add({ from: "bot", text: "Server se connect nahi ho paaya. API chal rahi hai?" });
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-neutral-200 bg-white px-4 md:h-16">
        <h1 className="font-semibold">Assistant</h1>
        {pending ? (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
            Working…
          </span>
        ) : null}
      </header>

      <div ref={listRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-5">
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.from === "me" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm shadow-sm sm:max-w-[70%] ${
                m.from === "me"
                  ? "rounded-tr-sm bg-[#25D366] text-white"
                  : "rounded-tl-sm bg-white text-neutral-800 ring-1 ring-neutral-200"
              }`}
            >
              {m.text}
              {m.href ? (
                <Link
                  href={m.href}
                  className="mt-2 block text-sm font-semibold text-[#075E54] underline underline-offset-2"
                >
                  Customers dekho →
                </Link>
              ) : null}
            </div>
          </div>
        ))}
        {pending ? <p className="text-sm text-neutral-400">working…</p> : null}
      </div>

      <form onSubmit={send} className="shrink-0 border-t border-neutral-200 bg-white p-3">
        {file ? (
          <div className="mb-2 flex items-center gap-2 rounded-lg bg-neutral-100 px-3 py-2 text-sm">
            <span className="truncate">{file.name}</span>
            <span className="shrink-0 text-neutral-500">{(file.size / 1024).toFixed(0)} KB</span>
            <button
              type="button"
              onClick={() => setFile(null)}
              className="ml-auto shrink-0 rounded px-1 text-neutral-500 hover:text-red-600"
              aria-label="Remove file"
            >
              ×
            </button>
          </div>
        ) : null}

        {recording ? (
          <div className="mb-2 flex items-center gap-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            <span className="h-2 w-2 animate-pulse rounded-full bg-red-600" />
            Recording {seconds}s
            <button
              type="button"
              onClick={stopRecording}
              className="ml-auto rounded-full bg-red-600 px-3 py-1 text-xs font-semibold text-white"
            >
              Stop
            </button>
          </div>
        ) : null}

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={pending || recording}
            className="shrink-0 rounded-full border border-neutral-300 px-3 py-2.5 text-base leading-none disabled:opacity-50"
            aria-label="Attach ZIP"
            title="Attach WhatsApp export (.zip)"
          >
            📎
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".zip,audio/*"
            className="hidden"
            onChange={(event) => {
              pick(event.target.files?.[0] ?? null);
              event.target.value = "";
            }}
          />

          <button
            type="button"
            onClick={recording ? stopRecording : startRecording}
            disabled={pending}
            className={`shrink-0 rounded-full border px-3 py-2.5 text-base leading-none disabled:opacity-50 ${
              recording ? "border-red-400 bg-red-50" : "border-neutral-300"
            }`}
            aria-label={recording ? "Stop recording" : "Record voice note"}
            title={recording ? "Stop recording" : "Record voice note"}
          >
            {recording ? "⏹" : "🎤"}
          </button>

          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder="Type or speak... e.g. Andheri ke customers dikhao"
            enterKeyHint="send"
            autoComplete="off"
            className="min-w-0 flex-1 rounded-full border border-neutral-300 px-4 py-2.5 text-base outline-none focus:border-[#075E54] focus:ring-2 focus:ring-[#075E54]/20"
          />
          <button
            type="submit"
            disabled={pending || recording || (!value.trim() && !file)}
            className="shrink-0 rounded-full bg-[#075E54] px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </>
  );
}
