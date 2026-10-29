const WA_LINK = `https://wa.me/917820986147?text=${encodeURIComponent(
  "Hi! I want to know how BrokerDesk can organise my property business.",
)}`;

const NAV = [
  { href: "#features", label: "Features" },
  { href: "#assistant", label: "Assistant" },
  { href: "#how", label: "How it works" },
  { href: "#faq", label: "FAQ" },
];

const FEATURES = [
  {
    key: "a",
    title: "Rental properties available",
    body: "Every flat a landlord sends you — BHK, rent, floor, ready-to-move — collected in one list instead of scrolling chats.",
  },
  {
    key: "b",
    title: "Landlords & tenants",
    body: "Who owns which flat, who is renting, who called yesterday, who is still chasing you.",
  },
  {
    key: "c",
    title: "Show calendar",
    body: "Who to show what, and when. This week's visits, pulled straight from your messages.",
  },
  {
    key: "d",
    title: "Brokerage due, collected, projected",
    body: "What you earned this month, what is still pending, what is coming. No more mental maths.",
  },
];

const EXAMPLES = [
  "How many appointments do I have this week?",
  "What brokerage did I earn this month?",
  "How many people contacted me for rent this month?",
  "Show me available rentals in Lokhandwala area",
];

const STEPS = [
  { n: "1", t: "You keep using WhatsApp", b: "Text and voice notes exactly as you do today. Nothing to change, nothing new to learn." },
  { n: "2", t: "The AI reads and organises", b: "It sorts every message into properties, people, appointments and brokerage by itself." },
  { n: "3", t: "Everything sits in one place", b: "Ask a question by typing or speaking — or open the dashboard and look." },
];

const FAQS = [
  {
    q: "Does this replace WhatsApp?",
    a: "No. WhatsApp stays exactly as it is. BrokerDesk reads from it and gives you a dashboard on top.",
  },
  {
    q: "Is my data safe?",
    a: "Your data lives in your own account. It is only used to build your dashboard — never sold, never shared.",
  },
  {
    q: "Does it work in Hindi / Hinglish?",
    a: "Yes. Ask by typing or by voice, in English or Hinglish, the way you actually talk.",
  },
];

function WaButton({ className = "" }: { className?: string }) {
  return (
    <a
      href={WA_LINK}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center gap-2 rounded-full bg-[#25D366] px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-[#1eb955] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#25D366] ${className}`}
    >
      <svg viewBox="0 0 24 24" aria-hidden className="h-5 w-5 fill-current">
        <path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0 0 12.04 2m0 1.67c2.2 0 4.27.86 5.83 2.42a8.2 8.2 0 0 1 2.42 5.82c0 4.54-3.7 8.24-8.25 8.24a8.24 8.24 0 0 1-4.2-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.19 8.19 0 0 1-1.26-4.38c0-4.54 3.7-8.24 8.25-8.24m-3.5 4.5c-.17 0-.44.06-.67.31-.23.25-.88.86-.88 2.1s.9 2.44 1.03 2.6c.13.17 1.75 2.67 4.25 3.74.59.26 1.06.41 1.42.53.6.19 1.14.16 1.57.1.48-.07 1.48-.6 1.69-1.19.21-.58.21-1.08.15-1.19-.06-.1-.23-.17-.48-.29-.25-.13-1.48-.73-1.71-.81-.23-.09-.4-.13-.56.12-.17.25-.64.81-.79.98-.15.17-.29.19-.54.06-.25-.12-1.06-.39-2.01-1.24-.74-.66-1.24-1.48-1.39-1.73-.15-.25-.02-.38.11-.51.11-.11.25-.29.37-.44.13-.15.17-.25.25-.42.08-.17.04-.31-.02-.44-.06-.12-.55-1.35-.77-1.84-.2-.48-.4-.42-.55-.43z" />
      </svg>
      Chat on WhatsApp
    </a>
  );
}

export default function Home() {
  return (
    <div className="min-h-screen bg-white text-neutral-900">
      <header className="sticky top-0 z-50 border-b border-neutral-200/80 bg-white/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-6">
          <a href="#" className="text-lg font-bold tracking-tight">
            Broker<span className="text-[#075E54]">Desk</span>
          </a>
          <nav className="hidden gap-5 text-sm font-medium text-neutral-600 md:flex">
            {NAV.map((n) => (
              <a key={n.href} href={n.href} className="hover:text-[#075E54]">
                {n.label}
              </a>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <a
              href="/login"
              className="rounded-full border border-neutral-300 px-4 py-2 text-sm font-medium hover:border-[#075E54] hover:text-[#075E54]"
            >
              Broker login
            </a>
            <WaButton className="hidden px-5 py-2 text-sm sm:inline-flex" />
          </div>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 md:grid-cols-2 md:py-24 md:items-center">
          <div>
            <span className="inline-block rounded-full bg-[#25D366]/10 px-3 py-1 text-sm font-semibold text-[#075E54]">
              Built for WhatsApp-first brokers
            </span>
            <h1 className="mt-4 text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl">
              Your WhatsApp is your office.
              <br />
              This is your <span className="text-[#075E54]">dashboard</span>.
            </h1>
            <p className="mt-4 max-w-lg text-lg text-neutral-600">
              Keep messaging exactly as you do today. BrokerDesk reads your WhatsApp Business
              chats and organises them into properties, people, appointments and brokerage.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-3">
              <WaButton />
              <a
                href="#how"
                className="rounded-full border border-neutral-300 px-6 py-3 font-semibold hover:border-[#075E54] hover:text-[#075E54]"
              >
                See how it works
              </a>
            </div>
          </div>

          <div className="rounded-3xl border border-neutral-200 bg-neutral-50 p-5 shadow-sm">
            <div className="rounded-2xl bg-[#E7F7EE] p-4">
              <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white p-3 text-sm shadow-sm">
                <p>
                  Bhai 2BHK available karna hai Andheri West, 45k, 3rd floor, ready to move.
                </p>
                <p className="mt-1 text-right text-xs text-neutral-500">10:42 ✓✓</p>
              </div>
              <div className="ml-auto mt-3 max-w-[85%] rounded-2xl rounded-tr-sm bg-[#25D366] p-3 text-sm text-white shadow-sm">
                <p>Saved: BHK 2 · Andheri West · ₹45,000/mo · Ready to move ✓</p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              {[
                ["₹82,000", "Brokerage this month"],
                ["7", "Shows this week"],
                ["23", "New rent enquiries"],
                ["14", "Active rentals"],
              ].map(([v, l]) => (
                <div key={l} className="rounded-xl border border-neutral-200 bg-white p-3">
                  <div className="text-xl font-bold">{v}</div>
                  <div className="text-neutral-500">{l}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Problem */}
        <section className="border-y border-neutral-200 bg-neutral-50">
          <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
            <div className="grid gap-6 md:grid-cols-3">
              {[
                ["Chats everywhere", "Landlords in one group, tenants in another, deals in your head."],
                ["No ledger", "You never know what you actually earned until you sit down and remember."],
                ["Missed visits", "Someone asked for a 4 pm showing four days ago. Was it Thursday?"],
              ].map(([t, b]) => (
                <div key={t}>
                  <h3 className="font-bold">{t}</h3>
                  <p className="mt-1 text-neutral-600">{b}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="mx-auto max-w-6xl px-4 py-16 scroll-mt-20 sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight">One app, four answers</h2>
          <p className="mt-2 max-w-2xl text-neutral-600">
            Everything your WhatsApp already contains, finally in one place.
          </p>
          <div className="mt-8 grid gap-5 sm:grid-cols-2">
            {FEATURES.map((f) => (
              <div
                key={f.key}
                className="rounded-2xl border border-neutral-200 p-6 transition hover:border-[#25D366] hover:shadow-sm"
              >
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#075E54] font-bold text-white">
                  {f.key}
                </span>
                <h3 className="mt-4 text-lg font-bold">{f.title}</h3>
                <p className="mt-2 text-neutral-600">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Assistant */}
        <section id="assistant" className="scroll-mt-20 border-y border-neutral-200 bg-[#075E54] text-white">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 md:grid-cols-2 md:items-center">
            <div>
              <h2 className="text-3xl font-bold tracking-tight">Just say it. Type or speak.</h2>
              <p className="mt-3 text-white/80">
                No menus to learn. Ask in English or Hinglish, by keyboard or by voice — the
                agent reads your data and answers.
              </p>
              <ul className="mt-6 space-y-3">
                {EXAMPLES.map((e) => (
                  <li
                    key={e}
                    className="rounded-xl bg-white/10 px-4 py-3 text-sm backdrop-blur ring-1 ring-white/15"
                  >
                    &ldquo;{e}&rdquo;
                  </li>
                ))}
              </ul>
            </div>
            <div className="overflow-hidden rounded-3xl bg-white shadow-xl">
              <iframe
                title="Available rentals in Lokhandwala, Mumbai"
                src="https://www.openstreetmap.org/export/embed.html?bbox=72.8120%2C19.1240%2C72.8580%2C19.1560&layer=mapnik&marker=19.1400%2C72.8350"
                className="h-72 w-full border-0"
                loading="lazy"
              />
              <p className="px-4 py-3 text-sm text-neutral-600">
                &ldquo;Show me available rentals in Lokhandwala area&rdquo; — pin drop on a free
                OpenStreetMap map.
              </p>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="mx-auto max-w-6xl px-4 py-16 scroll-mt-20 sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n} className="rounded-2xl border border-neutral-200 p-6">
                <div className="text-4xl font-extrabold text-[#25D366]">{s.n}</div>
                <h3 className="mt-3 font-bold">{s.t}</h3>
                <p className="mt-1 text-neutral-600">{s.b}</p>
              </div>
            ))}
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="border-t border-neutral-200 bg-neutral-50">
          <div className="mx-auto max-w-3xl px-4 py-16 scroll-mt-20 sm:px-6">
            <h2 className="text-3xl font-bold tracking-tight">Questions</h2>
            <div className="mt-6 divide-y divide-neutral-200">
              {FAQS.map((f) => (
                <details key={f.q} className="group py-4">
                  <summary className="cursor-pointer list-none font-semibold marker:hidden">
                    {f.q}
                    <span className="float-right text-[#075E54] transition group-open:rotate-45">
                      +
                    </span>
                  </summary>
                  <p className="mt-2 text-neutral-600">{f.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-6xl px-4 py-16 text-center sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight">Still managing your business in a chat?</h2>
          <p className="mx-auto mt-3 max-w-xl text-neutral-600">
            Send one message and see what BrokerDesk does with it.
          </p>
          <div className="mt-6 flex justify-center">
            <WaButton />
          </div>
        </section>
      </main>

      <footer className="border-t border-neutral-200 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 text-sm text-neutral-500 sm:flex-row sm:px-6">
          <p>
            Broker<span className="font-semibold text-neutral-700">Desk</span> — WhatsApp stays,
            the chaos doesn&apos;t.
          </p>
          <a href={WA_LINK} target="_blank" rel="noopener noreferrer" className="hover:text-[#075E54]">
            +91 78209 86147
          </a>
        </div>
      </footer>
    </div>
  );
}
