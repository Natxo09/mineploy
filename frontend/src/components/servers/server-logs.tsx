"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useWebSocket } from "@/hooks/use-websocket";
import { serverService } from "@/services/server.service";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  FileText,
  Download,
  Loader2,
  AlertCircle,
  ChevronDown,
  Clock,
} from "lucide-react";
import { useSystemSettings } from "@/hooks/use-system-settings";

interface ServerLogsProps {
  serverId: number;
  isRunning?: boolean;
}

export function ServerLogs({ serverId, isRunning = false }: ServerLogsProps) {
  const [autoScroll, setAutoScroll] = useState(true);
  const [logLines, setLogLines] = useState<string[]>([]);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { timezone } = useSystemSettings();

  // Fetch initial container logs when component mounts
  const { data: initialLogs, isLoading: logsLoading } = useQuery({
    queryKey: ["server-logs", serverId],
    queryFn: () => serverService.getServerLogsV2(serverId, 500, "docker"),
    enabled: isRunning, // Only fetch when server is running
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  });

  // Initialize logLines with fetched logs
  useEffect(() => {
    if (initialLogs?.logs) {
      const lines = initialLogs.logs
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.length > 0);
      setLogLines(lines);
    }
  }, [initialLogs]);

  // WebSocket for real-time container logs
  const { connected, logLines: wsLogLines } = useWebSocket({
    serverId,
    channel: "container_logs",
    enabled: isRunning, // Only connect when server is running
    onLogLine: (line) => {
      setLogLines((prev) => [...prev, line]);
    },
    onError: (error) => {
      console.error("WebSocket error:", error);
    },
  });

  // Auto-scroll to bottom when logs update
  useEffect(() => {
    if (autoScroll && scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [logLines, autoScroll]);

  // Download logs as text file
  const handleDownloadLogs = () => {
    if (logLines.length === 0) return;

    const content = logLines.join("\n");
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `server-${serverId}-logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Scroll to bottom manually
  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
        setAutoScroll(true);
      }
    }
  };

  // Clear logs
  const handleClearLogs = () => {
    setLogLines([]);
  };

  // Check for EULA warning
  const hasEulaError = logLines.some(
    (line) =>
      line.includes("eula.txt") || line.includes("You need to agree to the EULA")
  );

  // Format log line with colors
  const formatLogLine = (line: string, index: number) => {
    let colorClass = "text-foreground";
    let fontWeight = "";

    // Color by log level
    if (line.includes("[INFO]") || line.includes("INFO")) {
      colorClass = "text-blue-600 dark:text-blue-400";
    } else if (line.includes("[WARN]") || line.includes("WARN")) {
      colorClass = "text-yellow-600 dark:text-yellow-400";
      fontWeight = "font-medium";
    } else if (line.includes("[ERROR]") || line.includes("ERROR")) {
      colorClass = "text-red-600 dark:text-red-400";
      fontWeight = "font-semibold";
    } else if (line.includes("[DEBUG]") || line.includes("DEBUG")) {
      colorClass = "text-gray-500 dark:text-gray-400";
    } else if (line.includes("[init]") || line.includes("mc-image-helper")) {
      colorClass = "text-cyan-600 dark:text-cyan-400";
    } else if (line.includes("Starting") || line.includes("Done")) {
      colorClass = "text-green-600 dark:text-green-400";
      fontWeight = "font-medium";
    } else if (line.includes("Stopping") || line.includes("Saving")) {
      colorClass = "text-orange-600 dark:text-orange-400";
    } else if (line.includes("Unpacking")) {
      colorClass = "text-purple-600 dark:text-purple-400 text-opacity-70";
    }

    return (
      <div key={index} className={`${colorClass} ${fontWeight}`}>
        {line}
      </div>
    );
  };

  return (
    <>
      <Card className="flex flex-col h-[calc(100vh-20rem)] overflow-hidden py-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 h-12 border-b flex-shrink-0">
          <div className="flex items-center gap-2">
            <FileText className="size-4 text-muted-foreground" />
            <h3 className="font-semibold">Container Logs</h3>
            <Badge variant="outline">{logLines.length} lines</Badge>
            {connected && (
              <Badge variant="outline" className="text-xs">
                <span className="size-2 rounded-full bg-green-500 mr-1.5 inline-block" />
                Live
              </Badge>
            )}
            {hasEulaError && (
              <Badge variant="destructive" className="ml-2">
                <AlertCircle className="size-3 mr-1" />
                EULA Required
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoScroll(!autoScroll)}
            >
              {autoScroll ? "Auto-scroll: ON" : "Auto-scroll: OFF"}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={scrollToBottom}
              disabled={autoScroll}
            >
              <ChevronDown className="size-4" />
              Bottom
            </Button>

            <Separator orientation="vertical" className="h-6" />

            <Button
              variant="outline"
              size="sm"
              onClick={handleClearLogs}
              disabled={logLines.length === 0}
            >
              Clear
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadLogs}
              disabled={logLines.length === 0}
            >
              <Download className="size-4" />
              Download
            </Button>
          </div>
        </div>

        {/* EULA Warning */}
        {hasEulaError && (
          <div className="p-4 bg-destructive/10 border-b border-destructive/20 flex-shrink-0">
            <div className="flex items-start gap-3">
              <AlertCircle className="size-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-destructive">
                  EULA Agreement Required
                </p>
                <p className="text-sm text-muted-foreground">
                  The server requires you to accept the Minecraft EULA. You need to
                  manually edit the <code className="text-xs">eula.txt</code> file
                  in the server directory and change{" "}
                  <code className="text-xs">eula=false</code> to{" "}
                  <code className="text-xs">eula=true</code>, or use the file
                  manager when it's implemented.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Logs Content */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea ref={scrollAreaRef} className="h-full">
            <div className="p-4">
              {logsLoading ? (
                <div className="flex items-center justify-center min-h-[400px]">
                  <Loader2 className="size-8 animate-spin text-muted-foreground" />
                  <span className="ml-3 text-sm text-muted-foreground">
                    Loading logs...
                  </span>
                </div>
              ) : logLines.length > 0 ? (
                <div className="font-mono text-xs space-y-0.5">
                  {logLines.map((line, index) => formatLogLine(line, index))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center min-h-[400px] gap-2">
                  <FileText className="size-8 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    No logs available
                  </p>
                  <p className="text-xs text-muted-foreground">
                    New logs will appear here in real-time
                  </p>
                </div>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-3 h-10 border-t bg-muted/30 flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div
                className={`size-2 rounded-full ${
                  connected ? "bg-green-500" : "bg-gray-400 animate-pulse"
                }`}
              />
              {connected ? "Live streaming" : "Connecting..."}
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="size-3" />
              <span>{timezone || "Loading..."}</span>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Showing {logLines.length} lines
          </p>
        </div>
      </Card>
    </>
  );
}
