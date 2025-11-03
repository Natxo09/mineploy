"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Server } from "lucide-react";
import { LoginForm } from "@/components/auth/login-form";
import { SetupForm } from "@/components/auth/setup-form";
import { setupService } from "@/services/setup.service";
import { ThemeSwitcherWrapper } from "@/components/theme-switcher-wrapper";

export default function LoginPage() {
  const searchParams = useSearchParams();
  const setupSuccess = searchParams.get("setup") === "success";

  const [needsSetup, setNeedsSetup] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showSuccessMessage, setShowSuccessMessage] = useState(setupSuccess);

  useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const status = await setupService.getStatus();
        console.log("Setup status response:", status);
        console.log("setupSuccess param:", setupSuccess);

        // Always trust the backend status
        // If backend says setup is required, show setup form regardless of URL params
        console.log("Setting needsSetup to:", status.requires_setup);
        setNeedsSetup(status.requires_setup);

        // Clean up the URL param if setup is still needed
        if (status.requires_setup && setupSuccess) {
          console.log("Cleaning up stale setup=success param");
          window.history.replaceState({}, "", "/login");
        }
      } catch (error) {
        console.error("Failed to check setup status:", error);
        // Default to login if we can't check
        setNeedsSetup(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkSetupStatus();

    // Hide success message after 5 seconds
    if (setupSuccess) {
      const timer = setTimeout(() => setShowSuccessMessage(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [setupSuccess]);

  if (isLoading) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <div className="flex items-center gap-2 text-muted-foreground">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  console.log("Rendering login page. needsSetup:", needsSetup);

  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      {/* Left side - Flat design */}
      <div className="bg-muted relative hidden lg:flex flex-col items-start justify-between p-10">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="bg-primary text-primary-foreground flex size-10 items-center justify-center rounded-xl">
              <Server className="size-5" />
            </div>
            <h1 className="text-3xl font-bold">Mineploy</h1>
          </div>
          <p className="text-muted-foreground text-sm ml-[52px]">
            The open-source solution for managing Minecraft servers
          </p>
        </div>

        <div className="flex flex-col gap-8 max-w-md">
          <p className="text-muted-foreground text-lg">
            Deploy, manage, and monitor your Minecraft servers with ease. Built with modern technologies for developers and server administrators.
          </p>
          <ul className="text-sm text-muted-foreground space-y-2">
            <li>• Multi-version support: Vanilla, Paper, Spigot, Fabric, Forge & more</li>
            <li>• Docker-powered isolated containers</li>
            <li>• Real-time console with RCON integration</li>
            <li>• Automated backup scheduling and restoration</li>
            <li>• Role-based access control for teams</li>
            <li>• File management and configuration editor</li>
          </ul>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex justify-end items-center gap-2">
          <ThemeSwitcherWrapper />
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-xs">
            {showSuccessMessage && !needsSetup && (
              <div className="mb-4 p-3 text-sm text-green-700 bg-green-50 dark:bg-green-950/20 rounded-md border border-green-200 dark:border-green-900">
                Setup completed successfully! Please login with your credentials.
              </div>
            )}
            {needsSetup ? <SetupForm /> : <LoginForm />}
          </div>
        </div>
      </div>
    </div>
  );
}
