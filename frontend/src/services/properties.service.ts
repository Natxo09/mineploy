import apiClient from "@/lib/api-client";
import type { ServerProperties, UpdateServerPropertiesRequest } from "@/types";

/**
 * Server properties management service
 */
export const propertiesService = {
  /**
   * Get server properties configuration
   */
  async getProperties(serverId: number): Promise<ServerProperties> {
    const response = await apiClient.get<ServerProperties>(
      `/servers/${serverId}/properties`
    );
    return response.data;
  },

  /**
   * Update server properties configuration
   * Note: Some changes require server restart to take effect
   */
  async updateProperties(
    serverId: number,
    data: UpdateServerPropertiesRequest
  ): Promise<ServerProperties> {
    const response = await apiClient.patch<ServerProperties>(
      `/servers/${serverId}/properties`,
      data
    );
    return response.data;
  },
};
