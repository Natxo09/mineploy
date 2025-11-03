"use client";

import { useParams, useRouter } from "next/navigation";
import { useServer, useServerStats, useServerActions } from "@/hooks/use-servers";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft,
  Play,
  Square,
  RotateCw,
  Terminal,
  BarChart3,
  Settings,
  FolderOpen,
  Users,
  Loader2,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ServerStatus } from "@/types";
import { ServerConsole } from "@/components/console/server-console";
import { ServerStatsCharts } from "@/components/servers/server-stats-charts";
import { ServerLogs } from "@/components/servers/server-logs";
import { ServerSettings } from "@/components/servers/server-settings";

const statusConfig: Record<
  ServerStatus,
  { label: string; className: string; dotColor: string }
> = {
  running: {
    label: "Running",
    className: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
    dotColor: "bg-green-500",
  },
  stopped: {
    label: "Stopped",
    className: "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20",
    dotColor: "bg-red-500",
  },
  downloading: {
    label: "Downloading",
    className: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
    dotColor: "bg-orange-500",
  },
  initializing: {
    label: "Initializing",
    className: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
    dotColor: "bg-orange-500",
  },
  starting: {
    label: "Starting",
    className: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
    dotColor: "bg-orange-500",
  },
  stopping: {
    label: "Stopping",
    className: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
    dotColor: "bg-orange-500",
  },
  error: {
    label: "Error",
    className: "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20",
    dotColor: "bg-red-500",
  },
};

export default function ServerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const serverId = parseInt(params.id as string);

  const { data: server, isLoading, error } = useServer(serverId);
  const { data: stats } = useServerStats(serverId, {
    enabled: server?.status === "running",
  });
  const { startServer, stopServer, restartServer } = useServerActions();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !server) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] gap-4">
        <p className="text-muted-foreground">Server not found</p>
        <Button onClick={() => router.push("/servers")}>
          <ArrowLeft />
          Back to Servers
        </Button>
      </div>
    );
  }

  const statusInfo = statusConfig[server.status];
  const isTransitioning =
    server.status === "downloading" ||
    server.status === "initializing" ||
    server.status === "starting" ||
    server.status === "stopping";

  const handleStart = () => startServer.mutate(serverId);
  const handleStop = () => stopServer.mutate(serverId);
  const handleRestart = () => restartServer.mutate(serverId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/servers")}
            >
              <ArrowLeft />
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <div className={cn("size-2 rounded-full", statusInfo.dotColor)} />
                <h1 className="text-3xl font-bold tracking-tight">{server.name}</h1>
              </div>
              {server.description && (
                <p className="text-muted-foreground mt-1">{server.description}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 ml-14">
            <Badge variant="outline" className={cn("border", statusInfo.className)}>
              {statusInfo.label}
            </Badge>
            <Badge variant="outline">{server.server_type}</Badge>
            <Badge variant="outline">{server.version}</Badge>
            <Badge variant="outline">Port: {server.port}</Badge>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {server.status === "stopped" && !isTransitioning ? (
            <Button onClick={handleStart} disabled={startServer.isPending}>
              {startServer.isPending ? (
                <Loader2 className="animate-spin" />
              ) : (
                <Play />
              )}
              Start
            </Button>
          ) : server.status === "running" && !isTransitioning ? (
            <>
              <Button
                variant="outline"
                onClick={handleRestart}
                disabled={restartServer.isPending}
              >
                {restartServer.isPending ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <RotateCw />
                )}
                Restart
              </Button>
              <Button
                variant="outline"
                onClick={handleStop}
                disabled={stopServer.isPending}
              >
                {stopServer.isPending ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <Square />
                )}
                Stop
              </Button>
            </>
          ) : (
            <Button disabled>
              <Loader2 className="animate-spin" />
              {statusInfo.label}...
            </Button>
          )}
        </div>
      </div>

      <Separator />

      {/* Tabs */}
      <Tabs defaultValue="console" className="space-y-4">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="console">
            <Terminal className="size-4" />
            Console
          </TabsTrigger>
          <TabsTrigger value="logs">
            <FileText className="size-4" />
            Logs
          </TabsTrigger>
          <TabsTrigger value="stats">
            <BarChart3 className="size-4" />
            Stats
          </TabsTrigger>
          <TabsTrigger value="players" disabled>
            <Users className="size-4" />
            Players
          </TabsTrigger>
          <TabsTrigger value="files" disabled>
            <FolderOpen className="size-4" />
            Files
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="size-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="console" className="space-y-4">
          <ServerConsole
            serverId={serverId}
            isRunning={server.status === "running"}
          />
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <ServerLogs serverId={serverId} />
        </TabsContent>

        <TabsContent value="stats" className="space-y-4">
          <ServerStatsCharts
            stats={stats}
            server={server}
            isRunning={server.status === "running"}
          />
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <ServerSettings
            serverId={serverId}
            isRunning={server.status === "running"}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
