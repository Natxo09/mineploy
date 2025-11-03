"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dockerService } from "@/services/docker.service";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  HardDrive,
  Image,
  Container,
  Database,
  Network,
  Trash2,
  Loader2,
  AlertCircle,
  Info,
  AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth.store";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export default function SpacePage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const isAdmin = user?.role === "admin";

  const [confirmAction, setConfirmAction] = useState<{
    type: "images" | "containers" | "volumes" | "networks" | "all" | null;
    title: string;
    description: string;
  } | null>(null);

  // Fetch disk usage
  const {
    data: diskUsage,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["docker-disk-usage"],
    queryFn: () => dockerService.getDiskUsage(),
    enabled: isAdmin,
  });

  // Prune mutations
  const pruneImagesMutation = useMutation({
    mutationFn: () => dockerService.pruneImages(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["docker-disk-usage"] });
      toast.success("Images cleaned successfully", {
        description: `Deleted ${data.images_deleted} images, freed ${data.space_reclaimed_formatted}`,
      });
      setConfirmAction(null);
    },
    onError: (error: any) => {
      toast.error("Failed to clean images", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  const pruneContainersMutation = useMutation({
    mutationFn: () => dockerService.pruneContainers(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["docker-disk-usage"] });
      toast.success("Containers cleaned successfully", {
        description: `Deleted ${data.containers_deleted} containers, freed ${data.space_reclaimed_formatted}`,
      });
      setConfirmAction(null);
    },
    onError: (error: any) => {
      toast.error("Failed to clean containers", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  const pruneVolumesMutation = useMutation({
    mutationFn: () => dockerService.pruneVolumes(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["docker-disk-usage"] });
      toast.success("Volumes cleaned successfully", {
        description: `Deleted ${data.volumes_deleted} volumes, freed ${data.space_reclaimed_formatted}`,
      });
      setConfirmAction(null);
    },
    onError: (error: any) => {
      toast.error("Failed to clean volumes", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  const pruneNetworksMutation = useMutation({
    mutationFn: () => dockerService.pruneNetworks(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["docker-disk-usage"] });
      toast.success("Networks cleaned successfully", {
        description: `Deleted ${data.networks_deleted} networks`,
      });
      setConfirmAction(null);
    },
    onError: (error: any) => {
      toast.error("Failed to clean networks", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  const pruneAllMutation = useMutation({
    mutationFn: () => dockerService.pruneAll(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["docker-disk-usage"] });
      toast.success("Complete cleanup successful", {
        description: `Freed ${data.total_space_reclaimed_formatted} total`,
      });
      setConfirmAction(null);
    },
    onError: (error: any) => {
      toast.error("Failed to complete cleanup", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  const handleConfirm = () => {
    if (!confirmAction) return;

    switch (confirmAction.type) {
      case "images":
        pruneImagesMutation.mutate();
        break;
      case "containers":
        pruneContainersMutation.mutate();
        break;
      case "volumes":
        pruneVolumesMutation.mutate();
        break;
      case "networks":
        pruneNetworksMutation.mutate();
        break;
      case "all":
        pruneAllMutation.mutate();
        break;
    }
  };

  const isPending =
    pruneImagesMutation.isPending ||
    pruneContainersMutation.isPending ||
    pruneVolumesMutation.isPending ||
    pruneNetworksMutation.isPending ||
    pruneAllMutation.isPending;

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="size-12 text-muted-foreground" />
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold">Access Denied</h2>
          <p className="text-muted-foreground">
            You need administrator privileges to access this page.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2">
        <AlertCircle className="size-8 text-destructive" />
        <p className="text-sm text-muted-foreground">
          Failed to load Docker disk usage
        </p>
        <Button onClick={() => refetch()} variant="outline" size="sm">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <HardDrive className="size-8" />
              Space Management
            </h1>
            <p className="text-muted-foreground">
              Monitor Mineploy disk usage and cleanup unused Minecraft server resources
            </p>
          </div>
          <Button onClick={() => refetch()} variant="outline" disabled={isLoading}>
            {isLoading ? (
              <Loader2 className="size-4 mr-2 animate-spin" />
            ) : (
              <HardDrive className="size-4 mr-2" />
            )}
            Refresh
          </Button>
        </div>

        <Separator />

        {/* Total Usage Card */}
        <Card className="p-6 bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h2 className="text-2xl font-bold">Total Mineploy Disk Usage</h2>
                <p className="text-sm text-muted-foreground">
                  Space used by Minecraft server images and containers
                </p>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold">
                  {diskUsage?.total.size_formatted}
                </div>
                <Badge variant="outline" className="mt-2">
                  {((diskUsage?.images.count || 0) +
                    (diskUsage?.containers.count || 0) +
                    (diskUsage?.volumes.count || 0))}{" "}
                  total resources
                </Badge>
              </div>
            </div>
          </div>
        </Card>

        {/* Resource Cards */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Images */}
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Image className="size-5 text-blue-500" />
                    <h3 className="text-lg font-semibold">Unused Images</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Minecraft images not used by any server
                  </p>
                </div>
                <Badge variant="secondary">{diskUsage?.images.count || 0}</Badge>
              </div>
              <div className="text-2xl font-bold">
                {diskUsage?.images.size_formatted}
              </div>
              <Button
                onClick={() =>
                  setConfirmAction({
                    type: "images",
                    title: "Clean Unused Minecraft Images",
                    description:
                      "This will remove unused itzg/minecraft-server images. Only Minecraft server images not currently used by containers will be deleted. Other Docker images on your system will not be affected.",
                  })
                }
                variant="outline"
                className="w-full"
                disabled={isPending}
              >
                <Trash2 className="size-4 mr-2" />
                Clean Images
              </Button>
            </div>
          </Card>

          {/* Containers */}
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Container className="size-5 text-green-500" />
                    <h3 className="text-lg font-semibold">Stopped Containers</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Mineploy containers that are stopped
                  </p>
                </div>
                <Badge variant="secondary">
                  {diskUsage?.containers.count || 0}
                </Badge>
              </div>
              <div className="text-2xl font-bold">
                {diskUsage?.containers.size_formatted}
              </div>
              <Button
                onClick={() =>
                  setConfirmAction({
                    type: "containers",
                    title: "Clean Stopped Mineploy Containers",
                    description:
                      "This will remove stopped Mineploy-managed containers only. Running servers and other Docker containers will not be affected.",
                  })
                }
                variant="outline"
                className="w-full"
                disabled={isPending}
              >
                <Trash2 className="size-4 mr-2" />
                Clean Containers
              </Button>
            </div>
          </Card>

          {/* Volumes */}
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Database className="size-5 text-orange-500" />
                    <h3 className="text-lg font-semibold">Orphaned Volumes</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Unused volumes (not attached to any container)
                  </p>
                </div>
                <Badge variant="secondary">{diskUsage?.volumes.count || 0}</Badge>
              </div>
              <div className="text-2xl font-bold">
                {diskUsage?.volumes.size_formatted}
              </div>
              <Alert variant="destructive" className="mb-4">
                <AlertTriangle className="size-4" />
                <AlertDescription className="text-xs">
                  Warning: This will delete orphaned world data permanently
                </AlertDescription>
              </Alert>
              <Button
                onClick={() =>
                  setConfirmAction({
                    type: "volumes",
                    title: "Clean Unused Volumes",
                    description:
                      "WARNING: This will permanently delete orphaned Minecraft world data that is not attached to any container. This action cannot be undone.",
                  })
                }
                variant="outline"
                className="w-full"
                disabled={isPending}
              >
                <Trash2 className="size-4 mr-2" />
                Clean Volumes
              </Button>
            </div>
          </Card>

          {/* Networks */}
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Network className="size-5 text-purple-500" />
                    <h3 className="text-lg font-semibold">Networks</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Unused Docker networks
                  </p>
                </div>
              </div>
              <div className="text-2xl font-bold text-muted-foreground">N/A</div>
              <Button
                onClick={() =>
                  setConfirmAction({
                    type: "networks",
                    title: "Clean Unused Networks",
                    description:
                      "This will remove unused Docker networks. Networks in use will not be affected.",
                  })
                }
                variant="outline"
                className="w-full"
                disabled={isPending}
              >
                <Trash2 className="size-4 mr-2" />
                Clean Networks
              </Button>
            </div>
          </Card>
        </div>

        {/* Complete Cleanup */}
        <Card className="p-6 border-destructive/50">
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex-1 space-y-2">
                <h3 className="text-lg font-semibold text-destructive flex items-center gap-2">
                  <Trash2 className="size-5" />
                  Complete Cleanup
                </h3>
                <p className="text-sm text-muted-foreground">
                  Remove all unused Mineploy resources (Minecraft images, stopped containers, orphaned volumes, and unused networks) in one operation. Other Docker resources on your system will not be affected.
                </p>
                <Alert>
                  <Info className="size-4" />
                  <AlertDescription className="text-xs">
                    This will free the maximum amount of space but will permanently
                    delete orphaned world data. Make sure you have backups before
                    proceeding.
                  </AlertDescription>
                </Alert>
              </div>
            </div>
            <Button
              onClick={() =>
                setConfirmAction({
                  type: "all",
                  title: "Complete Mineploy Cleanup",
                  description:
                    "This will remove ALL unused Mineploy resources including unused Minecraft images, stopped containers, orphaned volumes, and unused networks. Other Docker resources will not be affected. This action cannot be undone and will permanently delete orphaned Minecraft world data. Are you absolutely sure?",
                })
              }
              variant="destructive"
              className="w-full"
              disabled={isPending}
            >
              <Trash2 className="size-4 mr-2" />
              Clean Everything
            </Button>
          </div>
        </Card>
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog
        open={confirmAction !== null}
        onOpenChange={(open) => !open && setConfirmAction(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmAction?.title}</AlertDialogTitle>
            <AlertDialogDescription>{confirmAction?.description}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirm}
              disabled={isPending}
              className={
                confirmAction?.type === "volumes" || confirmAction?.type === "all"
                  ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  : ""
              }
            >
              {isPending ? (
                <>
                  <Loader2 className="size-4 mr-2 animate-spin" />
                  Cleaning...
                </>
              ) : (
                "Confirm"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
