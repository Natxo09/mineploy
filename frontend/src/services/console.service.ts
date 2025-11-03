import apiClient from "@/lib/api-client";
import type { CommandRequest, CommandResponse, PlayerListResponse } from "@/types";

/**
 * Console and RCON service
 */
export const consoleService = {
  /**
   * Execute a command via RCON
   */
  async executeCommand(
    serverId: number,
    command: string
  ): Promise<CommandResponse> {
    const response = await apiClient.post<CommandResponse>(
      `/console/${serverId}/command`,
      { command } as CommandRequest
    );
    return response.data;
  },

  /**
   * Get list of online players
   */
  async getPlayers(serverId: number): Promise<PlayerListResponse> {
    const response = await apiClient.get<PlayerListResponse>(
      `/console/${serverId}/players`
    );
    return response.data;
  },
};
