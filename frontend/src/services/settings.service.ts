import apiClient from "@/lib/api-client";
import type { SystemSettings, SystemSettingsUpdate } from "@/types";

/**
 * System settings service
 */
export const settingsService = {
  /**
   * Get current system settings
   */
  async getSettings(): Promise<SystemSettings> {
    const response = await apiClient.get<SystemSettings>("/settings");
    return response.data;
  },

  /**
   * Update system settings (admin only)
   */
  async updateSettings(data: SystemSettingsUpdate): Promise<SystemSettings> {
    const response = await apiClient.put<SystemSettings>("/settings", data);
    return response.data;
  },
};
