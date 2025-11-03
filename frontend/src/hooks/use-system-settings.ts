import { useQuery } from "@tanstack/react-query";
import { settingsService } from "@/services/settings.service";

/**
 * Hook to access system settings, primarily for timezone configuration
 */
export function useSystemSettings() {
  const { data: settings, isLoading, error } = useQuery({
    queryKey: ["system-settings"],
    queryFn: () => settingsService.getSettings(),
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });

  return {
    settings,
    timezone: settings?.timezone,
    isLoading,
    error,
  };
}
