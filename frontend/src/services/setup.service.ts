import apiClient from "@/lib/api-client";
import type {
  SetupRequest,
  SetupResponse,
  SetupStatus,
} from "@/types";

/**
 * Setup wizard service
 */
export const setupService = {
  /**
   * Check if initial setup is required
   */
  async getStatus(): Promise<SetupStatus> {
    const response = await apiClient.get<SetupStatus>("/setup/status");
    return response.data;
  },

  /**
   * Initialize application with first admin user
   */
  async initialize(data: SetupRequest): Promise<SetupResponse> {
    const response = await apiClient.post<SetupResponse>("/setup/initialize", data);
    return response.data;
  },
};
