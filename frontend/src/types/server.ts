/**
 * Server types
 */

export enum ServerType {
  VANILLA = "vanilla",
  PAPER = "paper",
  SPIGOT = "spigot",
  FABRIC = "fabric",
  FORGE = "forge",
  NEOFORGE = "neoforge",
  PURPUR = "purpur",
}

export enum ServerStatus {
  STOPPED = "stopped",
  DOWNLOADING = "downloading",
  INITIALIZING = "initializing",
  STARTING = "starting",
  RUNNING = "running",
  STOPPING = "stopping",
  ERROR = "error",
}

export enum ServerPermission {
  VIEW = "view",
  CONSOLE = "console",
  START_STOP = "start_stop",
  FILES = "files",
  BACKUPS = "backups",
  MANAGE = "manage",
}

export interface Server {
  id: number;
  name: string;
  description: string | null;
  server_type: ServerType;
  version: string;
  port: number;
  rcon_port: number;
  memory_mb: number;
  container_id: string | null;
  container_name: string;
  status: ServerStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_started_at: string | null;
  last_stopped_at: string | null;
}

export interface CreateServerRequest {
  name: string;
  description?: string;
  server_type: ServerType;
  version: string;
  port?: number;
  rcon_port?: number;
  memory_mb?: number;
}

export interface UpdateServerRequest {
  name?: string;
  description?: string;
  memory_mb?: number;
}

export interface ServerStats {
  server_id: number;
  status: ServerStatus;
  online_players: number;
  max_players: number;
  cpu_usage: number;
  memory_usage: number;
  memory_limit: number;
  uptime_seconds: number;
}

export interface ServerList {
  id: number;
  name: string;
  description: string | null;
  server_type: ServerType;
  version: string;
  port: number;
  status: ServerStatus;
  is_active: boolean;
  memory_mb: number;
  created_at: string;
}

export interface UserServerPermission {
  id: number;
  user_id: number;
  server_id: number;
  permissions: ServerPermission[];
  created_at: string;
  updated_at: string;
}

export interface ServerLogs {
  logs: string;
  lines: number;
}
