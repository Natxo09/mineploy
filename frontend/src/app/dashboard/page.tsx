"use client";

import { useAuthStore } from "@/stores/auth.store";

export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <>
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome back, {user?.username}!
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
          <h3 className="font-semibold mb-2">Servers</h3>
          <p className="text-muted-foreground text-sm">
            No servers yet. Create your first server to get started.
          </p>
        </div>
        <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
          <h3 className="font-semibold mb-2">Quick Actions</h3>
          <p className="text-muted-foreground text-sm">
            Server management coming soon.
          </p>
        </div>
        <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
          <h3 className="font-semibold mb-2">System Status</h3>
          <p className="text-muted-foreground text-sm">
            All systems operational.
          </p>
        </div>
      </div>
    </>
  );
}
