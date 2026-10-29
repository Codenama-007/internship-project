import Sidebar from "@/components/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    // dvh keeps the chat input above the mobile browser bar
    <div className="flex h-dvh flex-col md:flex-row">
      <Sidebar />
      <main className="flex min-h-0 flex-1 flex-col">{children}</main>
    </div>
  );
}
