"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { serverService } from "@/services/server.service";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  FileText,
  RefreshCw,
  Download,
  Loader2,
  AlertCircle,
  ChevronDown,
} from "lucide-react";

interface ServerLogsProps {
  serverId: number;
}

export function ServerLogs({ serverId }: ServerLogsProps) {
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Fetch logs
  const {
    data: logsData,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["server-logs", serverId],
    queryFn: () => serverService.getServerLogs(serverId, 1000),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
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
  }, [logsData, autoScroll]);

  // Download logs as text file
  const handleDownloadLogs = () => {
    if (!logsData?.logs) return;

    const blob = new Blob([logsData.logs], { type: "text/plain" });
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

  // Check for EULA warning
  const hasEulaError =
    logsData?.logs?.includes("eula.txt") ||
    logsData?.logs?.includes("You need to agree to the EULA");

  return (
    <Card className="flex flex-col h-[calc(100vh-20rem)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <FileText className="size-4 text-muted-foreground" />
          <h3 className="font-semibold">Container Logs</h3>
          <Badge variant="outline">{logsData?.lines ?? 0} lines</Badge>
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
            onClick={() => refetch()}
            disabled={isFetching}
          >
            {isFetching ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCw className="size-4" />
            )}
            Refresh
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadLogs}
            disabled={!logsData?.logs}
          >
            <Download className="size-4" />
            Download
          </Button>
        </div>
      </div>

      {/* EULA Warning */}
      {hasEulaError && (
        <div className="p-4 bg-destructive/10 border-b border-destructive/20">
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
      <ScrollArea
        ref={scrollAreaRef}
        className="flex-1 p-4"
        onScroll={(e) => {
          // Detect if user scrolled up manually
          const target = e.target as HTMLElement;
          const isAtBottom =
            target.scrollHeight - target.scrollTop === target.clientHeight;
          if (!isAtBottom && autoScroll) {
            setAutoScroll(false);
          }
        }}
      >
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-center">
            <AlertCircle className="size-8 text-destructive" />
            <p className="text-sm text-muted-foreground">
              Failed to load logs
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        ) : logsData?.logs ? (
          <pre className="font-mono text-xs whitespace-pre-wrap break-words">
            {logsData.logs}
          </pre>
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-2">
            <FileText className="size-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No logs available</p>
          </div>
        )}
      </ScrollArea>

      {/* Footer */}
      <div className="flex items-center justify-between p-3 border-t bg-muted/30">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div
            className={`size-2 rounded-full ${
              isFetching ? "bg-blue-500 animate-pulse" : "bg-green-500"
            }`}
          />
          {isFetching ? "Refreshing..." : "Auto-refresh every 5s"}
        </div>
        <p className="text-xs text-muted-foreground">
          Showing last {logsData?.lines ?? 0} lines
        </p>
      </div>
    </Card>
  );
}
