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
  ExternalLink,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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

interface ServerTableProps {
  servers: ServerList[];
}

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

const serverTypeConfig: Record<ServerType, { label: string; color: string }> = {
  vanilla: { label: "Vanilla", color: "bg-amber-500" },
  paper: { label: "Paper", color: "bg-orange-500" },
  spigot: { label: "Spigot", color: "bg-yellow-500" },
  fabric: { label: "Fabric", color: "bg-purple-500" },
  forge: { label: "Forge", color: "bg-blue-500" },
  neoforge: { label: "NeoForge", color: "bg-indigo-500" },
  purpur: { label: "Purpur", color: "bg-violet-500" },
};

export function ServerTable({ servers }: ServerTableProps) {
  const { startServer, stopServer, restartServer, deleteServer } = useServerActions();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [serverToDelete, setServerToDelete] = useState<ServerList | null>(null);

  const handleDeleteClick = (server: ServerList) => {
    setServerToDelete(server);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (serverToDelete) {
      deleteServer.mutate(serverToDelete.id, {
        onSuccess: () => {
          setDeleteDialogOpen(false);
          setServerToDelete(null);
        },
      });
    }
  };

  return (
    <>
      <div className="rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[250px]">Server</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Version</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Players</TableHead>
            <TableHead>Memory</TableHead>
            <TableHead>Port</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="w-[100px] text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {servers.length === 0 ? (
            <TableRow>
              <TableCell colSpan={9} className="h-24 text-center">
                No servers found
              </TableCell>
            </TableRow>
          ) : (
            servers.map((server) => {
              const statusInfo = statusConfig[server.status];
              const typeInfo = serverTypeConfig[server.server_type];
              const memoryPercentage = 65; // Mockup data

              const isTransitioning =
                server.status === "starting" ||
                server.status === "stopping";

              return (
                <TableRow key={server.id} className="group">
                  {/* Server Name */}
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className={cn("size-2 rounded-full", statusInfo.dotColor)} />
                      <div className="min-w-0">
                        <p className="font-medium truncate">{server.name}</p>
                        {server.description && (
                          <p className="text-xs text-muted-foreground truncate">
                            {server.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </TableCell>

                  {/* Type */}
                  <TableCell>
                    <Badge variant="outline">{typeInfo.label}</Badge>
                  </TableCell>

                  {/* Version */}
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {server.version}
                    </span>
                  </TableCell>

                  {/* Status */}
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn("border", statusInfo.className)}
                    >
                      {statusInfo.label}
                    </Badge>
                  </TableCell>

                  {/* Players */}
                  <TableCell>
                    <div className="flex items-center gap-1.5 text-sm">
                      <span className="font-medium">
                        {server.status === "running" ? "12" : "0"}
                      </span>
                      <span className="text-muted-foreground">/</span>
                      <span className="text-muted-foreground">20</span>
                    </div>
                  </TableCell>

                  {/* Memory */}
                  <TableCell>
                    <div className="space-y-1 min-w-[120px]">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">
                          {server.status === "running"
                            ? `${((server.memory_mb * memoryPercentage) / 100 / 1024).toFixed(1)} GB`
                            : "0 GB"}
                        </span>
                        <span className="font-medium">
                          {(server.memory_mb / 1024).toFixed(1)} GB
                        </span>
                      </div>
                      <Progress
                        value={server.status === "running" ? memoryPercentage : 0}
                        className="h-1"
                      />
                    </div>
                  </TableCell>

                  {/* Port */}
                  <TableCell>
                    <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                      {server.port}
                    </code>
                  </TableCell>

                  {/* Created */}
                  <TableCell>
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(server.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </TableCell>

                  {/* Actions */}
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      {server.status === "stopped" && !isTransitioning ? (
                        <Button
                          size="icon-sm"
                          variant="ghost"
                          onClick={() => startServer.mutate(server.id)}
                          disabled={startServer.isPending}
                        >
                          <Play className="size-3.5" />
                        </Button>
                      ) : server.status === "running" && !isTransitioning ? (
                        <>
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            onClick={() => restartServer.mutate(server.id)}
                            disabled={restartServer.isPending}
                          >
                            <RotateCw className="size-3.5" />
                          </Button>
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            onClick={() => stopServer.mutate(server.id)}
                            disabled={stopServer.isPending}
                          >
                            <Square className="size-3.5" />
                          </Button>
                        </>
                      ) : (
                        <Button size="icon-sm" variant="ghost" disabled>
                          <RotateCw className="size-3.5 animate-spin" />
                        </Button>
                      )}

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button size="icon-sm" variant="ghost">
                            <MoreVertical className="size-3.5" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <ExternalLink />
                            Open
                          </DropdownMenuItem>
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
                            onClick={() => handleDeleteClick(server)}
                          >
                            <Trash2 />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>

    {/* Delete Dialog */}
    <DeleteDialog
      open={deleteDialogOpen}
      onOpenChange={setDeleteDialogOpen}
      onConfirm={handleDeleteConfirm}
      title="Delete Server"
      description="This action cannot be undone. This will permanently delete the server and its container."
      itemName={serverToDelete?.name}
      isDeleting={deleteServer.isPending}
      requireConfirmation={true}
    />
    </>
  );
}
