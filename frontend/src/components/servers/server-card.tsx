"use client";

import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import {
  Play,
  Square,
  RotateCw,
  MoreVertical,
  Settings,
  Trash2,
  Activity,
  HardDrive,
  Users,
} from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import { DeleteDialog } from "@/components/ui/delete-dialog";
import { useServerActions } from "@/hooks/use-servers";
import type { ServerList, ServerStatus, ServerType } from "@/types";
import { cn } from "@/lib/utils";

interface ServerCardProps {
  server: ServerList;
}

const statusConfig: Record<
  ServerStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline"; className: string; dotColor: string }
> = {
  running: {
    label: "Running",
    variant: "default",
    className: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
    dotColor: "bg-green-500",
  },
  stopped: {
    label: "Stopped",
    variant: "destructive",
    className: "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20",
    dotColor: "bg-red-500",
  },
  downloading: {
    label: "Downloading",
    variant: "default",
    className: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
    dotColor: "bg-orange-500",
  },
  initializing: {
    label: "Initializing",
    variant: "default",
    className: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
    dotColor: "bg-orange-500",
  },
  starting: {
    label: "Starting",
    variant: "default",
    className: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
    dotColor: "bg-orange-500",
  },
  stopping: {
    label: "Stopping",
    variant: "default",
    className: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
    dotColor: "bg-orange-500",
  },
  error: {
    label: "Error",
    variant: "destructive",
    className: "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20",
    dotColor: "bg-red-500",
  },
};

const serverTypeConfig: Record<ServerType, { label: string; color: string }> = {
  vanilla: { label: "Vanilla", color: "bg-amber-500" },
  paper: { label: "Paper", color: "bg-orange-500" },
  spigot: { label: "Spigot", color: "bg-yellow-500" },
  fabric: { label: "Fabric", color: "bg-purple-500" },
  forge: { label: "Forge", color: "bg-blue-500" },
  neoforge: { label: "NeoForge", color: "bg-indigo-500" },
  purpur: { label: "Purpur", color: "bg-violet-500" },
};

export function ServerCard({ server }: ServerCardProps) {
  const statusInfo = statusConfig[server.status];
  const typeInfo = serverTypeConfig[server.server_type];
  const { startServer, stopServer, restartServer, deleteServer } = useServerActions();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const isTransitioning =
    server.status === "downloading" ||
    server.status === "initializing" ||
    server.status === "starting" ||
    server.status === "stopping" ||
    startServer.isPending ||
    stopServer.isPending ||
    restartServer.isPending;

  const handleStart = () => {
    startServer.mutate(server.id);
  };

  const handleStop = () => {
    stopServer.mutate(server.id);
  };

  const handleRestart = () => {
    restartServer.mutate(server.id);
  };

  const handleDelete = () => {
    deleteServer.mutate(server.id, {
      onSuccess: () => {
        setDeleteDialogOpen(false);
      },
    });
  };

  const memoryPercentage = 65; // Mockup data - will come from stats API

  return (
    <Card className="group hover:shadow-md transition-all cursor-pointer">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <div className={cn("size-2 rounded-full", statusInfo.dotColor)} />
              <h3 className="font-semibold truncate">{server.name}</h3>
            </div>
            {server.description && (
              <p className="text-sm text-muted-foreground line-clamp-1">
                {server.description}
              </p>
            )}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon-sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreVertical />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Settings />
                Settings
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Activity />
                View Stats
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => setDeleteDialogOpen(true)}
              >
                <Trash2 />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Delete Dialog */}
        <DeleteDialog
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          onConfirm={handleDelete}
          title="Delete Server"
          description="This action cannot be undone. This will permanently delete the server and its container."
          itemName={server.name}
          isDeleting={deleteServer.isPending}
          requireConfirmation={true}
        />

        <div className="flex items-center gap-2 mt-2">
          <Badge variant="outline" className={cn("border", statusInfo.className)}>
            {statusInfo.label}
          </Badge>
          <Badge variant="outline">
            {typeInfo.label}
          </Badge>
          <Badge variant="outline">
            {server.version}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <div className="space-y-3">
          {/* Memory Usage */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <HardDrive className="size-3.5" />
                <span>Memory</span>
              </div>
              <span className="font-medium">
                {server.status === "running"
                  ? `${((server.memory_mb * memoryPercentage) / 100 / 1024).toFixed(1)} / ${(server.memory_mb / 1024).toFixed(1)} GB`
                  : `${(server.memory_mb / 1024).toFixed(1)} GB`}
              </span>
            </div>
            <Progress
              value={server.status === "running" ? memoryPercentage : 0}
              className="h-1.5"
            />
          </div>

          {/* Server Info */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="flex items-center gap-2 text-xs">
              <Activity className="size-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Port:</span>
              <span className="font-medium">{server.port}</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <Users className="size-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Players:</span>
              <span className="font-medium">
                {server.status === "running" ? "12/20" : "0/20"}
              </span>
            </div>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-0 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {formatDistanceToNow(new Date(server.created_at), { addSuffix: true })}
        </p>

        <div className="flex items-center gap-1">
          {server.status === "stopped" && !isTransitioning ? (
            <Button
              size="icon-sm"
              variant="outline"
              onClick={handleStart}
              disabled={isTransitioning}
            >
              <Play className="size-3.5" />
            </Button>
          ) : server.status === "running" && !isTransitioning ? (
            <>
              <Button
                size="icon-sm"
                variant="outline"
                onClick={handleRestart}
                disabled={isTransitioning}
              >
                <RotateCw className="size-3.5" />
              </Button>
              <Button
                size="icon-sm"
                variant="outline"
                onClick={handleStop}
                disabled={isTransitioning}
              >
                <Square className="size-3.5" />
              </Button>
            </>
          ) : (
            <Button size="icon-sm" variant="outline" disabled>
              <RotateCw className="size-3.5 animate-spin" />
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}
