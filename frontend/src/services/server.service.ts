import apiClient from "@/lib/api-client";
import type {
  Server,
  ServerList,
  ServerStats,
  ServerLogs,
  CreateServerRequest,
  UpdateServerRequest,
} from "@/types";

/**
 * Server management service
 */
export const serverService = {
  /**
   * Get all accessible servers
   */
  async getServers(): Promise<ServerList[]> {
    const response = await apiClient.get<ServerList[]>("/servers");
    return response.data;
  },

  /**
   * Get server by ID
   */
  async getServer(id: number): Promise<Server> {
    const response = await apiClient.get<Server>(`/servers/${id}`);
    return response.data;
  },

  /**
   * Create new server
   */
  async createServer(data: CreateServerRequest): Promise<Server> {
    const response = await apiClient.post<Server>("/servers", data);
    return response.data;
  },

  /**
   * Update server settings
   */
  async updateServer(id: number, data: UpdateServerRequest): Promise<Server> {
    const response = await apiClient.put<Server>(`/servers/${id}`, data);
    return response.data;
  },

  /**
   * Delete server
   */
  async deleteServer(id: number): Promise<void> {
    await apiClient.delete(`/servers/${id}`);
  },

  /**
   * Start server
   */
  async startServer(id: number): Promise<Server> {
    const response = await apiClient.post<Server>(`/servers/${id}/start`);
    return response.data;
  },

  /**
   * Stop server
   */
  async stopServer(id: number): Promise<Server> {
    const response = await apiClient.post<Server>(`/servers/${id}/stop`);
    return response.data;
  },

  /**
   * Restart server
   */
  async restartServer(id: number): Promise<Server> {
    const response = await apiClient.post<Server>(`/servers/${id}/restart`);
    return response.data;
  },

  /**
   * Get server real-time statistics
   */
  async getServerStats(id: number): Promise<ServerStats> {
    const response = await apiClient.get<ServerStats>(`/servers/${id}/stats`);
    return response.data;
  },

  /**
   * Get server container logs
   */
  async getServerLogs(id: number, tail: number = 500): Promise<ServerLogs> {
    const response = await apiClient.get<ServerLogs>(
      `/servers/${id}/logs?tail=${tail}`
    );
    return response.data;
  },
};
