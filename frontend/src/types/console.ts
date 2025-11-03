/**
 * Console and RCON types
 */

export interface CommandRequest {
  command: string;
}

export interface CommandResponse {
  command: string;
  response: string;
  success: boolean;
}

export interface Player {
  name: string;
}

export interface PlayerListResponse {
  online_players: number;
  max_players: number;
  players: Player[];
}
