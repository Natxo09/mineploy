import { useEffect, useRef, useState, useCallback } from "react";

interface WebSocketMessage {
  type: "status_update" | "download_progress" | "logs" | "pong";
  server_id: number;
  status?: string;
  details?: Record<string, any>;
  current?: number;
  total?: number;
  percentage?: number;
  logs?: string;
}

interface UseWebSocketOptions {
  serverId: number;
  enabled?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onStatusUpdate?: (status: string, details?: Record<string, any>) => void;
  onLog?: (log: string) => void;
}

export function useWebSocket({
  serverId,
  enabled = true,
  onMessage,
  onStatusUpdate,
  onLog,
}: UseWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // Use refs to store callbacks to avoid recreating connection on callback changes
  const onMessageRef = useRef(onMessage);
  const onStatusUpdateRef = useRef(onStatusUpdate);
  const onLogRef = useRef(onLog);

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
    onStatusUpdateRef.current = onStatusUpdate;
    onLogRef.current = onLog;
  }, [onMessage, onStatusUpdate, onLog]);

  const connect = useCallback(() => {
    if (!enabled || wsRef.current) return;

    // Get WebSocket URL from API URL
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const wsUrl = apiUrl.replace(/^http/, "ws");
    const url = `${wsUrl}/servers/ws/${serverId}`;

    console.log("Connecting to WebSocket:", url);

    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log("WebSocket connected");
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log("WebSocket message:", message);

        // Call the generic onMessage handler using ref
        onMessageRef.current?.(message);

        // Handle specific message types
        if (message.type === "status_update" && message.status) {
          onStatusUpdateRef.current?.(message.status, message.details);
        } else if (message.type === "logs" && message.logs) {
          setLogs((prev) => [...prev, message.logs!]);
          onLogRef.current?.(message.logs);
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setConnected(false);
      wsRef.current = null;
    };

    wsRef.current = ws;
  }, [enabled, serverId]); // Removed callback dependencies - using refs instead

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setConnected(false);
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && connected) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, [connected]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  useEffect(() => {
    if (!enabled) return;

    connect();

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, serverId]); // Solo reconectar si cambia enabled o serverId

  return {
    connected,
    logs,
    sendMessage,
    clearLogs,
    disconnect,
  };
}
