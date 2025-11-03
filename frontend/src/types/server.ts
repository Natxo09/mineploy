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
  port: number;
  memory_mb?: number;
}

export interface UpdateServerRequest {
  name?: string;
  description?: string;
  memory_mb?: number;
}

export interface UserServerPermission {
  id: number;
  user_id: number;
  server_id: number;
  permissions: ServerPermission[];
  created_at: string;
  updated_at: string;
}
