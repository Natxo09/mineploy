"use client";

import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth/auth-guard";
import { useAuthStore } from "@/stores/auth.store";
import { Button } from "@/components/ui/button";
import { Server } from "lucide-react";
import { ThemeSwitcherWrapper } from "@/components/theme-switcher-wrapper";
import { toast } from "sonner";

function DashboardContent() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    toast.success("Logged out successfully", {
      description: "See you next time!",
    });

    logout();

    setTimeout(() => {
      router.push("/login");
    }, 500);
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-primary text-primary-foreground flex size-8 items-center justify-center rounded-lg">
              <Server className="size-4" />
            </div>
            <h1 className="text-xl font-bold">Mineploy</h1>
          </div>
          <div className="flex items-center gap-4">
            <ThemeSwitcherWrapper />
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                {user?.username} ({user?.role})
              </span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-6">
          <div>
            <h2 className="text-3xl font-bold">Dashboard</h2>
            <p className="text-muted-foreground mt-2">
              Welcome back, {user?.username}!
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="p-6 border rounded-lg">
              <h3 className="font-semibold mb-2">Servers</h3>
              <p className="text-muted-foreground text-sm">
                No servers yet. Create your first server to get started.
              </p>
            </div>
            <div className="p-6 border rounded-lg">
              <h3 className="font-semibold mb-2">Quick Actions</h3>
              <p className="text-muted-foreground text-sm">
                Server management coming soon.
              </p>
            </div>
            <div className="p-6 border rounded-lg">
              <h3 className="font-semibold mb-2">System Status</h3>
              <p className="text-muted-foreground text-sm">
                All systems operational.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardContent />
    </AuthGuard>
  );
}
