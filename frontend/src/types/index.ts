/**
 * Central export for all types
 */

export * from "./auth";
export * from "./server";
export * from "./setup";
export * from "./console";
export * from "./settings";
export * from "./properties";
export * from "./docker";

/**
 * Log and WebSocket streaming types
 */

export interface LogsResponse {
  logs: string;
  lines: number;
  filtered?: string | null;
}

export type WebSocketChannel = "default" | "minecraft_logs" | "container_logs";

export type WebSocketMessageType =
  | "status_update"
  | "download_progress"
  | "logs"
  | "log_line"
  | "pong"
  | "error";

export interface WebSocketMessage {
  type: WebSocketMessageType;
  server_id: number;
}

export interface WebSocketStatusUpdate extends WebSocketMessage {
  type: "status_update";
  status: string;
  details?: Record<string, any>;
}

export interface WebSocketDownloadProgress extends WebSocketMessage {
  type: "download_progress";
  current: number;
  total: number;
  percentage: number;
}

export interface WebSocketLogsMessage extends WebSocketMessage {
  type: "logs";
  logs: string;
}

export interface WebSocketLogLine extends WebSocketMessage {
  type: "log_line";
  line: string;
  channel: string;
}

export interface WebSocketPongMessage extends WebSocketMessage {
  type: "pong";
}

export interface WebSocketErrorMessage extends WebSocketMessage {
  type: "error";
  message: string;
}

export type WebSocketMessageUnion =
  | WebSocketStatusUpdate
  | WebSocketDownloadProgress
  | WebSocketLogsMessage
  | WebSocketLogLine
  | WebSocketPongMessage
  | WebSocketErrorMessage;

export type LogFilterType = "minecraft" | "docker" | null;
