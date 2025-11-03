/**
 * Docker cleanup and disk usage types
 */

export interface DiskUsageItem {
  size: number;
  size_formatted: string;
  count?: number;
}

export interface DiskUsage {
  images: DiskUsageItem;
  containers: DiskUsageItem;
  volumes: DiskUsageItem;
  build_cache: {
    size: number;
    size_formatted: string;
  };
  total: {
    size: number;
    size_formatted: string;
  };
}

export interface PruneImagesResult {
  images_deleted: number;
  space_reclaimed: number;
  space_reclaimed_formatted: string;
}

export interface PruneContainersResult {
  containers_deleted: number;
  space_reclaimed: number;
  space_reclaimed_formatted: string;
}

export interface PruneVolumesResult {
  volumes_deleted: number;
  space_reclaimed: number;
  space_reclaimed_formatted: string;
}

export interface PruneNetworksResult {
  networks_deleted: number;
}

export interface PruneAllResult {
  images: PruneImagesResult;
  containers: PruneContainersResult;
  volumes: PruneVolumesResult;
  networks: PruneNetworksResult;
  total_space_reclaimed: number;
  total_space_reclaimed_formatted: string;
}
