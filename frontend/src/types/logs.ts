/**
 * Log and WebSocket streaming types
 */

/**
 * Enhanced logs response with filtering support
 */
export interface LogsResponse {
  logs: string;
  lines: number;
  filtered?: string | null;
}

/**
 * WebSocket channel types
 */
export type WebSocketChannel = "default" | "minecraft_logs" | "container_logs";

/**
 * WebSocket message types
 */
export type WebSocketMessageType =
  | "status_update"
  | "download_progress"
  | "logs"
  | "log_line"
  | "pong"
  | "error";

/**
 * Base WebSocket message structure
 */
export interface WebSocketMessage {
  type: WebSocketMessageType;
  server_id: number;
}

/**
 * Status update message
 */
export interface WebSocketStatusUpdate extends WebSocketMessage {
  type: "status_update";
  status: string;
  details?: Record<string, any>;
}

/**
 * Download progress message
 */
export interface WebSocketDownloadProgress extends WebSocketMessage {
  type: "download_progress";
  current: number;
  total: number;
  percentage: number;
}

/**
 * Legacy logs message (bulk logs)
 */
export interface WebSocketLogsMessage extends WebSocketMessage {
  type: "logs";
  logs: string;
}

/**
 * Log line message (streaming)
 */
export interface WebSocketLogLine extends WebSocketMessage {
  type: "log_line";
  line: string;
  channel: string;
}

/**
 * Pong message (keepalive response)
 */
export interface WebSocketPongMessage extends WebSocketMessage {
  type: "pong";
}

/**
 * Error message
 */
export interface WebSocketErrorMessage extends WebSocketMessage {
  type: "error";
  message: string;
}

/**
 * Union type for all WebSocket messages
 */
export type WebSocketMessageUnion =
  | WebSocketStatusUpdate
  | WebSocketDownloadProgress
  | WebSocketLogsMessage
  | WebSocketLogLine
  | WebSocketPongMessage
  | WebSocketErrorMessage;

/**
 * Log filter types
 */
export type LogFilterType = "minecraft" | "docker" | null;
