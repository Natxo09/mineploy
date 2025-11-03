"use client";

import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Cpu,
  MemoryStick,
  Users,
  Clock,
  Activity,
  Server as ServerIcon,
  HardDrive,
} from "lucide-react";
import type { ServerStats, Server } from "@/types";
import { cn } from "@/lib/utils";

interface ServerStatsProps {
  stats: ServerStats | undefined;
  server: Server;
  isRunning: boolean;
}

export function ServerStatsComponent({
  stats,
  server,
  isRunning,
}: ServerStatsProps) {
  // Format uptime
  const formatUptime = (seconds: number) => {
    if (seconds === 0) return "0s";

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

    return parts.join(" ");
  };

  // Calculate memory percentage
  const memoryPercentage =
    stats?.memory_limit && stats.memory_limit > 0
      ? (stats.memory_usage / stats.memory_limit) * 100
      : 0;

  // Calculate player percentage
  const playerPercentage =
    stats?.max_players && stats.max_players > 0
      ? (stats.online_players / stats.max_players) * 100
      : 0;

  const getPercentageColor = (percentage: number) => {
    if (percentage >= 90) return "text-red-500 dark:text-red-400";
    if (percentage >= 70) return "text-orange-500 dark:text-orange-400";
    return "text-green-500 dark:text-green-400";
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return "bg-red-500";
    if (percentage >= 70) return "bg-orange-500";
    return "bg-green-500";
  };

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* CPU Usage Card */}
        <Card className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">
                CPU Usage
              </p>
              <div className="flex items-baseline gap-2">
                <p
                  className={cn(
                    "text-3xl font-bold",
                    getPercentageColor(stats?.cpu_usage ?? 0)
                  )}
                >
                  {isRunning ? (stats?.cpu_usage?.toFixed(1) ?? "0.0") : "0.0"}
                </p>
                <span className="text-muted-foreground">%</span>
              </div>
            </div>
            <div className="rounded-full bg-blue-500/10 p-2">
              <Cpu className="size-5 text-blue-500" />
            </div>
          </div>
          <Progress
            value={isRunning ? stats?.cpu_usage ?? 0 : 0}
            className="mt-4 h-2"
            indicatorClassName={getProgressColor(stats?.cpu_usage ?? 0)}
          />
        </Card>

        {/* Memory Usage Card */}
        <Card className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">
                Memory Usage
              </p>
              <div className="flex items-baseline gap-2">
                <p
                  className={cn(
                    "text-3xl font-bold",
                    getPercentageColor(memoryPercentage)
                  )}
                >
                  {isRunning
                    ? (stats?.memory_usage?.toFixed(0) ?? "0")
                    : "0"}
                </p>
                <span className="text-muted-foreground text-sm">
                  / {stats?.memory_limit?.toFixed(0) ?? server.memory_mb} MB
                </span>
              </div>
            </div>
            <div className="rounded-full bg-purple-500/10 p-2">
              <MemoryStick className="size-5 text-purple-500" />
            </div>
          </div>
          <Progress
            value={isRunning ? memoryPercentage : 0}
            className="mt-4 h-2"
            indicatorClassName={getProgressColor(memoryPercentage)}
          />
          <p className="text-xs text-muted-foreground mt-2">
            {memoryPercentage.toFixed(1)}% used
          </p>
        </Card>

        {/* Players Card */}
        <Card className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">
                Online Players
              </p>
              <div className="flex items-baseline gap-2">
                <p className="text-3xl font-bold">
                  {isRunning ? (stats?.online_players ?? 0) : 0}
                </p>
                <span className="text-muted-foreground text-sm">
                  / {stats?.max_players ?? 20}
                </span>
              </div>
            </div>
            <div className="rounded-full bg-green-500/10 p-2">
              <Users className="size-5 text-green-500" />
            </div>
          </div>
          <Progress
            value={isRunning ? playerPercentage : 0}
            className="mt-4 h-2"
            indicatorClassName="bg-green-500"
          />
          <p className="text-xs text-muted-foreground mt-2">
            {playerPercentage.toFixed(1)}% capacity
          </p>
        </Card>

        {/* Uptime Card */}
        <Card className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">
                Uptime
              </p>
              <p className="text-3xl font-bold">
                {isRunning
                  ? formatUptime(stats?.uptime_seconds ?? 0)
                  : "Offline"}
              </p>
            </div>
            <div className="rounded-full bg-orange-500/10 p-2">
              <Clock className="size-5 text-orange-500" />
            </div>
          </div>
          <div className="mt-4">
            <Badge variant={isRunning ? "default" : "secondary"}>
              {isRunning ? "Running" : "Stopped"}
            </Badge>
          </div>
        </Card>
      </div>

      {/* Server Information */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <ServerIcon className="size-5 text-muted-foreground" />
          <h3 className="font-semibold">Server Information</h3>
        </div>
        <Separator className="mb-4" />

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Server Type</p>
            <p className="font-medium capitalize">{server.server_type}</p>
          </div>

          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Version</p>
            <p className="font-medium">{server.version}</p>
          </div>

          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Server Port</p>
            <p className="font-medium">{server.port}</p>
          </div>

          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">RCON Port</p>
            <p className="font-medium">{server.rcon_port}</p>
          </div>

          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Container Name</p>
            <p className="font-medium font-mono text-sm">
              {server.container_name}
            </p>
          </div>

          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Status</p>
            <Badge variant={isRunning ? "default" : "secondary"}>
              {server.status}
            </Badge>
          </div>

          {server.last_started_at && (
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Last Started</p>
              <p className="font-medium text-sm">
                {new Date(server.last_started_at).toLocaleString()}
              </p>
            </div>
          )}

          {server.last_stopped_at && (
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Last Stopped</p>
              <p className="font-medium text-sm">
                {new Date(server.last_stopped_at).toLocaleString()}
              </p>
            </div>
          )}

          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Created</p>
            <p className="font-medium text-sm">
              {new Date(server.created_at).toLocaleString()}
            </p>
          </div>
        </div>
      </Card>

      {/* Resource Details */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* CPU Details */}
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="size-5 text-blue-500" />
            <h3 className="font-semibold">CPU Details</h3>
          </div>
          <Separator className="mb-4" />

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Current Usage</span>
              <span
                className={cn(
                  "font-semibold",
                  getPercentageColor(stats?.cpu_usage ?? 0)
                )}
              >
                {isRunning ? `${stats?.cpu_usage?.toFixed(2)}%` : "N/A"}
              </span>
            </div>
            <Progress
              value={isRunning ? stats?.cpu_usage ?? 0 : 0}
              className="h-3"
              indicatorClassName={getProgressColor(stats?.cpu_usage ?? 0)}
            />
            <p className="text-xs text-muted-foreground">
              {stats?.cpu_usage && stats.cpu_usage > 80
                ? "High CPU usage detected. Consider optimizing or upgrading."
                : isRunning
                ? "CPU usage is within normal range."
                : "Server is offline."}
            </p>
          </div>
        </Card>

        {/* Memory Details */}
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <HardDrive className="size-5 text-purple-500" />
            <h3 className="font-semibold">Memory Details</h3>
          </div>
          <Separator className="mb-4" />

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Used</span>
              <span className="font-semibold">
                {isRunning
                  ? `${stats?.memory_usage?.toFixed(0)} MB`
                  : "0 MB"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Allocated</span>
              <span className="font-semibold">
                {stats?.memory_limit?.toFixed(0) ?? server.memory_mb} MB
              </span>
            </div>
            <Progress
              value={isRunning ? memoryPercentage : 0}
              className="h-3"
              indicatorClassName={getProgressColor(memoryPercentage)}
            />
            <p className="text-xs text-muted-foreground">
              {memoryPercentage > 90
                ? "Memory usage is critically high. Consider increasing allocation."
                : memoryPercentage > 70
                ? "Memory usage is high but manageable."
                : isRunning
                ? "Memory usage is within normal range."
                : "Server is offline."}
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
