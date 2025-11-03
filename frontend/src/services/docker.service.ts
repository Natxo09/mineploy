import apiClient from "@/lib/api-client";
import type {
  DiskUsage,
  PruneImagesResult,
  PruneContainersResult,
  PruneVolumesResult,
  PruneNetworksResult,
  PruneAllResult,
} from "@/types/docker";

/**
 * Docker cleanup and monitoring service
 * Admin-only operations for managing Docker resources
 */
export const dockerService = {
  /**
   * Get Docker disk usage statistics
   * Shows space used by images, containers, volumes, and build cache
   */
  async getDiskUsage(): Promise<DiskUsage> {
    const response = await apiClient.get<DiskUsage>("/docker/disk-usage");
    return response.data;
  },

  /**
   * Remove unused Docker images
   * This will delete all images not referenced by any container
   */
  async pruneImages(): Promise<PruneImagesResult> {
    const response = await apiClient.post<PruneImagesResult>(
      "/docker/prune-images"
    );
    return response.data;
  },

  /**
   * Remove stopped containers
   * This will delete all stopped containers
   */
  async pruneContainers(): Promise<PruneContainersResult> {
    const response = await apiClient.post<PruneContainersResult>(
      "/docker/prune-containers"
    );
    return response.data;
  },

  /**
   * Remove unused volumes
   * WARNING: This will permanently delete orphaned Minecraft world data
   */
  async pruneVolumes(): Promise<PruneVolumesResult> {
    const response = await apiClient.post<PruneVolumesResult>(
      "/docker/prune-volumes"
    );
    return response.data;
  },

  /**
   * Remove unused networks
   * This will delete networks not used by any container
   */
  async pruneNetworks(): Promise<PruneNetworksResult> {
    const response = await apiClient.post<PruneNetworksResult>(
      "/docker/prune-networks"
    );
    return response.data;
  },

  /**
   * Perform complete cleanup of all unused Docker resources
   * This will remove:
   * - Unused images
   * - Stopped containers
   * - Unused volumes (WARNING: includes orphaned world data)
   * - Unused networks
   * - Build cache
   */
  async pruneAll(): Promise<PruneAllResult> {
    const response = await apiClient.post<PruneAllResult>("/docker/prune-all");
    return response.data;
  },
};
