import { useEffect, useRef, useState, useCallback } from "react";
import type {
  WebSocketMessageUnion,
  WebSocketChannel,
  WebSocketLogLine,
} from "@/types";

interface UseWebSocketOptions {
  serverId: number;
  channel?: WebSocketChannel;
  enabled?: boolean;
  onMessage?: (message: WebSocketMessageUnion) => void;
  onStatusUpdate?: (status: string, details?: Record<string, any>) => void;
  onLog?: (log: string) => void;
  onLogLine?: (line: string) => void; // For real-time streaming
  onError?: (error: string) => void; // For error messages
}

export function useWebSocket({
  serverId,
  channel = "default",
  enabled = true,
  onMessage,
  onStatusUpdate,
  onLog,
  onLogLine,
  onError,
}: UseWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [logLines, setLogLines] = useState<string[]>([]); // For streaming lines
  const wsRef = useRef<WebSocket | null>(null);

  // Use refs to store callbacks to avoid recreating connection on callback changes
  const onMessageRef = useRef(onMessage);
  const onStatusUpdateRef = useRef(onStatusUpdate);
  const onLogRef = useRef(onLog);
  const onLogLineRef = useRef(onLogLine);
  const onErrorRef = useRef(onError);

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
    onStatusUpdateRef.current = onStatusUpdate;
    onLogRef.current = onLog;
    onLogLineRef.current = onLogLine;
    onErrorRef.current = onError;
  }, [onMessage, onStatusUpdate, onLog, onLogLine, onError]);

  const connect = useCallback(() => {
    if (!enabled || wsRef.current) return;

    // Get WebSocket URL from API URL
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const wsUrl = apiUrl.replace(/^http/, "ws");
    const url = `${wsUrl}/servers/ws/${serverId}?channel=${channel}`;

    console.log("Connecting to WebSocket:", url, "channel:", channel);

    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log("WebSocket connected to channel:", channel);
      setConnected(true);

      // Send ping to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, 30000); // Every 30 seconds

      // Store interval to clear on disconnect
      (ws as any)._pingInterval = pingInterval;
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessageUnion = JSON.parse(event.data);

        // Call the generic onMessage handler using ref
        onMessageRef.current?.(message);

        // Handle specific message types
        if (message.type === "status_update" && "status" in message) {
          onStatusUpdateRef.current?.(message.status, message.details);
        } else if (message.type === "logs" && "logs" in message) {
          setLogs((prev) => [...prev, message.logs]);
          onLogRef.current?.(message.logs);
        } else if (message.type === "log_line" && "line" in message) {
          // Real-time log streaming
          const logLineMsg = message as WebSocketLogLine;
          setLogLines((prev) => [...prev, logLineMsg.line]);
          onLogLineRef.current?.(logLineMsg.line);
        } else if (message.type === "error" && "message" in message) {
          // Error message from server
          console.warn("WebSocket error message:", message.message);
          onErrorRef.current?.(message.message);
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected from channel:", channel);
      setConnected(false);
      wsRef.current = null;

      // Clear ping interval
      if ((ws as any)._pingInterval) {
        clearInterval((ws as any)._pingInterval);
      }
    };

    wsRef.current = ws;
  }, [enabled, serverId, channel]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      // Clear ping interval
      if ((wsRef.current as any)._pingInterval) {
        clearInterval((wsRef.current as any)._pingInterval);
      }

      wsRef.current.close();
      wsRef.current = null;
      setConnected(false);
    }
  }, []);

  const sendMessage = useCallback(
    (message: string) => {
      if (wsRef.current && connected) {
        wsRef.current.send(message);
      }
    },
    [connected]
  );

  const startStreaming = useCallback(() => {
    sendMessage("start_streaming");
  }, [sendMessage]);

  const stopStreaming = useCallback(() => {
    sendMessage("stop_streaming");
  }, [sendMessage]);

  const clearLogs = useCallback(() => {
    setLogs([]);
    setLogLines([]);
  }, []);

  useEffect(() => {
    if (!enabled) return;

    connect();

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, serverId, channel]); // Reconnect if serverId or channel changes

  return {
    connected,
    logs, // Legacy bulk logs
    logLines, // Real-time streaming lines
    sendMessage,
    startStreaming,
    stopStreaming,
    clearLogs,
    disconnect,
  };
}
