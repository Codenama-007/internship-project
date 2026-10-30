"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

// shortcut: labels are inert until Phase 2 routes exist — ceiling: no active state or
// navigation. Upgrade: swap each <span> for <Link href="/app/properties"> once built.
const TABS = ["Properties", "People", "Calendar", "Brokerage"];

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();

  async function logout() {
    await fetch("/api/logout", { method: "POST" }).catch(() => {});
    router.replace("/login");
    router.refresh();
  }

  const links = [
    { href: "/app", label: "Assistant" },
    { href: "/app/customers", label: "Customers" },
  ];

  return (
    <aside className="shrink-0 border-b border-neutral-200 bg-white md:h-full md:w-64 md:border-b-0 md:border-r">
      <div className="flex h-14 items-center gap-3 px-4 md:h-16">
        <Link href="/app" className="text-lg font-bold tracking-tight">
          Broker<span className="text-[#075E54]">Desk</span>
        </Link>
        <button
          onClick={logout}
          className="ml-auto rounded-full border border-neutral-300 px-4 py-1.5 text-sm font-medium hover:border-red-400 hover:text-red-600"
        >
          Logout
        </button>
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:pb-0">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium md:w-full ${
              pathname === link.href
                ? "bg-[#075E54]/10 text-[#075E54]"
                : "text-neutral-700 hover:bg-neutral-100"
            }`}
          >
            {link.label}
          </Link>
        ))}
        {TABS.map((tab) => (
          <span
            key={tab}
            className="whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium text-neutral-400 md:w-full"
          >
            {tab}
          </span>
        ))}
      </nav>
    </aside>
  );
}
