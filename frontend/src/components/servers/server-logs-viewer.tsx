"use client";

import { useEffect, useRef } from "react";
import { Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

interface ServerLogsViewerProps {
  logs: string[];
  className?: string;
  title?: string;
}

export function ServerLogsViewer({ logs, className, title = "Server Logs" }: ServerLogsViewerProps) {
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className={cn("flex flex-col rounded-lg border bg-card", className)}>
      {/* Header */}
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <Terminal className="size-4 text-muted-foreground" />
        <h3 className="font-semibold text-sm">{title}</h3>
        <span className="ml-auto text-xs text-muted-foreground">
          {logs.length} {logs.length === 1 ? "line" : "lines"}
        </span>
      </div>

      {/* Logs Container */}
      <div className="flex-1 overflow-auto bg-black/95 text-green-400 font-mono text-xs p-4 min-h-[300px] max-h-[500px]">
        {logs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p>Waiting for logs...</p>
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log, index) => (
              <div key={index} className="flex gap-2">
                <span className="text-green-600 select-none shrink-0">{(index + 1).toString().padStart(3, "0")}</span>
                <span className="whitespace-pre-wrap break-all">{log}</span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}
