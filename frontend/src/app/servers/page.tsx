"use client";

import { useState } from "react";
import {
  LayoutGrid,
  Table as TableIcon,
  Plus,
  Search,
  Filter,
  Loader2,
  AlertCircle,
  Server,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ServerCard } from "@/components/servers/server-card";
import { ServerTable } from "@/components/servers/server-table";
import { CreateServerDialog } from "@/components/servers/create-server-dialog";
import { useServers } from "@/hooks/use-servers";

type ViewMode = "grid" | "table";

export default function ServersPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Fetch servers from API
  const { data: servers = [], isLoading, isError, error } = useServers();

  // Filter servers based on search
  const filteredServers = servers.filter((server) => {
    const query = searchQuery.toLowerCase();
    return (
      server.name.toLowerCase().includes(query) ||
      server.description?.toLowerCase().includes(query) ||
      server.server_type.toLowerCase().includes(query)
    );
  });

  return (
    <>
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Server className="size-8 text-muted-foreground" />
            <h1 className="text-3xl font-bold tracking-tight">Servers</h1>
          </div>
          <p className="text-muted-foreground mt-1">
            Manage and monitor your Minecraft servers
          </p>
        </div>
        <Button size="default" onClick={() => setCreateDialogOpen(true)}>
          <Plus />
          New Server
        </Button>
      </div>

      {/* Filters and View Toggle */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Search servers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon-sm">
            <Filter />
          </Button>

          <ToggleGroup
            type="single"
            value={viewMode}
            onValueChange={(value) => {
              if (value) setViewMode(value as ViewMode);
            }}
            className="border rounded-md p-1"
          >
            <ToggleGroupItem value="grid" aria-label="Grid view" size="sm">
              <LayoutGrid className="size-4" />
            </ToggleGroupItem>
            <ToggleGroupItem value="table" aria-label="Table view" size="sm">
              <TableIcon className="size-4" />
            </ToggleGroupItem>
          </ToggleGroup>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="size-8 animate-spin text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Loading servers...</p>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            {(error as any)?.response?.data?.detail ||
              "Failed to load servers. Please try again."}
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Summary */}
      {!isLoading && !isError && (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Total</p>
                <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-bold text-primary">
                    {servers.length}
                  </span>
                </div>
              </div>
              <p className="text-2xl font-bold mt-2">{servers.length}</p>
            </div>

            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Running</p>
                <div className="size-8 rounded-full bg-green-500/10 flex items-center justify-center">
                  <span className="text-sm font-bold text-green-600 dark:text-green-400">
                    {servers.filter((s) => s.status === "running").length}
                  </span>
                </div>
              </div>
              <p className="text-2xl font-bold mt-2">
                {servers.filter((s) => s.status === "running").length}
              </p>
            </div>

            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Stopped</p>
                <div className="size-8 rounded-full bg-gray-500/10 flex items-center justify-center">
                  <span className="text-sm font-bold text-gray-600 dark:text-gray-400">
                    {servers.filter((s) => s.status === "stopped").length}
                  </span>
                </div>
              </div>
              <p className="text-2xl font-bold mt-2">
                {servers.filter((s) => s.status === "stopped").length}
              </p>
            </div>

            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Memory</p>
                <div className="size-8 rounded-full bg-blue-500/10 flex items-center justify-center">
                  <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
                    GB
                  </span>
                </div>
              </div>
              <p className="text-2xl font-bold mt-2">
                {(
                  servers.reduce((acc, s) => acc + s.memory_mb, 0) / 1024
                ).toFixed(1)}
              </p>
            </div>
          </div>

          {/* Content */}
          {filteredServers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="rounded-full bg-muted p-4 mb-4">
            <Search className="size-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No servers found</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery
              ? "Try adjusting your search query"
              : "Create your first server to get started"}
          </p>
          {!searchQuery && (
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus />
              New Server
            </Button>
          )}
        </div>
      ) : viewMode === "grid" ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredServers.map((server) => (
            <ServerCard key={server.id} server={server} />
          ))}
        </div>
      ) : (
        <ServerTable servers={filteredServers} />
      )}
        </>
      )}

      {/* Create Server Dialog */}
      <CreateServerDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
    </>
  );
}
