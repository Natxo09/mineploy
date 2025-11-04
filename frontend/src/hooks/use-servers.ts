import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { serverService } from "@/services/server.service";
import type { CreateServerRequest, UpdateServerRequest } from "@/types";
import { toast } from "sonner";

/**
 * Query keys for server-related queries
 */
export const serverKeys = {
  all: ["servers"] as const,
  lists: () => [...serverKeys.all, "list"] as const,
  list: (filters?: Record<string, unknown>) =>
    [...serverKeys.lists(), filters] as const,
  details: () => [...serverKeys.all, "detail"] as const,
  detail: (id: number) => [...serverKeys.details(), id] as const,
  stats: (id: number) => [...serverKeys.all, "stats", id] as const,
};

/**
 * Hook to fetch all servers
 */
export function useServers() {
  return useQuery({
    queryKey: serverKeys.lists(),
    queryFn: () => serverService.getServers(),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to fetch a single server by ID
 */
export function useServer(id: number) {
  return useQuery({
    queryKey: serverKeys.detail(id),
    queryFn: () => serverService.getServer(id),
    enabled: !!id,
    staleTime: 10000, // 10 seconds
  });
}

/**
 * Hook to fetch server stats
 */
export function useServerStats(id: number, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: serverKeys.stats(id),
    queryFn: () => serverService.getServerStats(id),
    enabled: options?.enabled ?? true,
    refetchInterval: 15000, // Refresh every 15 seconds (CPU/RAM change frequently)
    staleTime: 0, // Always consider stale for real-time updates
  });
}

/**
 * Hook for server actions (start, stop, restart, delete)
 */
export function useServerActions() {
  const queryClient = useQueryClient();

  const startServer = useMutation({
    mutationFn: (id: number) => serverService.startServer(id),
    onMutate: async (id) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: serverKeys.detail(id) });
      await queryClient.cancelQueries({ queryKey: serverKeys.lists() });

      // Optimistically update to starting state
      queryClient.setQueryData(serverKeys.detail(id), (old: any) => {
        if (!old) return old;
        return { ...old, status: "starting" };
      });

      toast.loading("Starting server...", { id: `start-${id}` });
    },
    onSuccess: (data) => {
      // Update cache with new data
      queryClient.setQueryData(serverKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.success("Server started successfully", { id: `start-${data.id}` });
    },
    onError: (error: any, id) => {
      // Revert optimistic update
      queryClient.invalidateQueries({ queryKey: serverKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.error(error.response?.data?.detail || "Failed to start server", {
        id: `start-${id}`,
      });
    },
  });

  const stopServer = useMutation({
    mutationFn: (id: number) => serverService.stopServer(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: serverKeys.detail(id) });
      await queryClient.cancelQueries({ queryKey: serverKeys.lists() });

      queryClient.setQueryData(serverKeys.detail(id), (old: any) => {
        if (!old) return old;
        return { ...old, status: "stopping" };
      });

      toast.loading("Stopping server...", { id: `stop-${id}` });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(serverKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.success("Server stopped successfully", { id: `stop-${data.id}` });
    },
    onError: (error: any, id) => {
      queryClient.invalidateQueries({ queryKey: serverKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.error(error.response?.data?.detail || "Failed to stop server", {
        id: `stop-${id}`,
      });
    },
  });

  const restartServer = useMutation({
    mutationFn: (id: number) => serverService.restartServer(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: serverKeys.detail(id) });
      await queryClient.cancelQueries({ queryKey: serverKeys.lists() });

      queryClient.setQueryData(serverKeys.detail(id), (old: any) => {
        if (!old) return old;
        return { ...old, status: "starting" };
      });

      toast.loading("Restarting server...", { id: `restart-${id}` });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(serverKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.success("Server restarted successfully", {
        id: `restart-${data.id}`,
      });
    },
    onError: (error: any, id) => {
      queryClient.invalidateQueries({ queryKey: serverKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.error(error.response?.data?.detail || "Failed to restart server", {
        id: `restart-${id}`,
      });
    },
  });

  const deleteServer = useMutation({
    mutationFn: (id: number) => serverService.deleteServer(id),
    onMutate: async (id) => {
      toast.loading("Deleting server...", { id: `delete-${id}` });
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      queryClient.removeQueries({ queryKey: serverKeys.detail(id) });
      toast.success("Server deleted successfully", { id: `delete-${id}` });
    },
    onError: (error: any, id) => {
      toast.error(error.response?.data?.detail || "Failed to delete server", {
        id: `delete-${id}`,
      });
    },
  });

  const createServer = useMutation({
    mutationFn: (data: CreateServerRequest) => serverService.createServer(data),
    onMutate: () => {
      toast.loading("Creating server...", { id: "create-server" });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.success(`Server "${data.name}" created successfully`, {
        id: "create-server",
      });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create server", {
        id: "create-server",
      });
    },
  });

  const updateServer = useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: UpdateServerRequest;
    }) => serverService.updateServer(id, data),
    onMutate: async ({ id }) => {
      toast.loading("Updating server...", { id: `update-${id}` });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(serverKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.success("Server updated successfully", { id: `update-${data.id}` });
    },
    onError: (error: any, { id }) => {
      toast.error(error.response?.data?.detail || "Failed to update server", {
        id: `update-${id}`,
      });
    },
  });

  return {
    startServer,
    stopServer,
    restartServer,
    deleteServer,
    createServer,
    updateServer,
  };
}
