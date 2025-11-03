"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";
import {
  Cpu,
  MemoryStick,
  Users,
  Clock,
  Activity,
  Server as ServerIcon,
} from "lucide-react";
import type { ServerStats, Server } from "@/types";
import { cn } from "@/lib/utils";
import { formatDateTime } from "@/lib/date-utils";
import { useSystemSettings } from "@/hooks/use-system-settings";

interface ServerStatsChartsProps {
  stats: ServerStats | undefined;
  server: Server;
  isRunning: boolean;
}

interface HistoricalDataPoint {
  time: string;
  cpu: number;
  memory: number;
  players: number;
  timestamp: number;
}

const MAX_DATA_POINTS = 60; // Keep last 60 data points (5 minutes at 5s interval)

export function ServerStatsCharts({
  stats,
  server,
  isRunning,
}: ServerStatsChartsProps) {
  const { timezone } = useSystemSettings();
  const [historicalData, setHistoricalData] = useState<HistoricalDataPoint[]>([]);

  // Update historical data when stats change
  useEffect(() => {
    if (stats && isRunning) {
      const now = Date.now();
      const timeLabel = new Date(now).toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      });

      setHistoricalData((prev) => {
        const newData = [
          ...prev,
          {
            time: timeLabel,
            cpu: stats.cpu_usage,
            memory: stats.memory_usage,
            players: stats.online_players,
            timestamp: now,
          },
        ];

        // Keep only the last MAX_DATA_POINTS
        if (newData.length > MAX_DATA_POINTS) {
          return newData.slice(-MAX_DATA_POINTS);
        }

        return newData;
      });
    } else if (!isRunning) {
      // Clear data when server stops
      setHistoricalData([]);
    }
  }, [stats, isRunning]);

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

  const chartConfig = {
    cpu: {
      label: "CPU",
      color: "hsl(var(--chart-1))",
    },
    memory: {
      label: "Memory",
      color: "hsl(var(--chart-2))",
    },
    players: {
      label: "Players",
      color: "hsl(var(--chart-3))",
    },
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

      {/* Charts */}
      <div className="grid gap-4">
        {/* CPU Chart */}
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="size-5 text-blue-500" />
            <h3 className="font-semibold">CPU Usage History</h3>
          </div>
          <Separator className="mb-4" />

          {historicalData.length > 0 ? (
            <div className="h-[300px] w-full">
              <ChartContainer config={chartConfig} className="h-full w-full">
                <AreaChart data={historicalData} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                  <defs>
                    <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor="hsl(var(--chart-1))"
                        stopOpacity={0.3}
                      />
                      <stop
                        offset="95%"
                        stopColor="hsl(var(--chart-1))"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveEnd"
                    minTickGap={30}
                    dy={10}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}%`}
                    width={45}
                  />
                  <ChartTooltip
                    content={
                      <ChartTooltipContent
                        formatter={(value) => `${Number(value).toFixed(1)}%`}
                      />
                    }
                  />
                  <Area
                    type="monotone"
                    dataKey="cpu"
                    stroke="hsl(var(--chart-1))"
                    fill="url(#cpuGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ChartContainer>
            </div>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              {isRunning ? "Collecting data..." : "Server is not running"}
            </div>
          )}
        </Card>

        {/* Memory Chart */}
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <MemoryStick className="size-5 text-purple-500" />
            <h3 className="font-semibold">Memory Usage History</h3>
          </div>
          <Separator className="mb-4" />

          {historicalData.length > 0 ? (
            <div className="h-[300px] w-full">
              <ChartContainer config={chartConfig} className="h-full w-full">
                <AreaChart data={historicalData} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                  <defs>
                    <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor="hsl(var(--chart-2))"
                        stopOpacity={0.3}
                      />
                      <stop
                        offset="95%"
                        stopColor="hsl(var(--chart-2))"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveEnd"
                    minTickGap={30}
                    dy={10}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, stats?.memory_limit ?? server.memory_mb]}
                    tickFormatter={(value) => `${Math.round(value)}`}
                    width={55}
                  />
                  <ChartTooltip
                    content={
                      <ChartTooltipContent
                        formatter={(value) => `${Number(value).toFixed(0)} MB`}
                      />
                    }
                  />
                  <Area
                    type="monotone"
                    dataKey="memory"
                    stroke="hsl(var(--chart-2))"
                    fill="url(#memoryGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ChartContainer>
            </div>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              {isRunning ? "Collecting data..." : "Server is not running"}
            </div>
          )}
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
                {formatDateTime(server.last_started_at, undefined, timezone)}
              </p>
            </div>
          )}

          {server.last_stopped_at && (
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Last Stopped</p>
              <p className="font-medium text-sm">
                {formatDateTime(server.last_stopped_at, undefined, timezone)}
              </p>
            </div>
          )}

          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Created</p>
            <p className="font-medium text-sm">
              {formatDateTime(server.created_at, undefined, timezone)}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
