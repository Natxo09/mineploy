"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Image from "next/image";
import { consoleService } from "@/services/console.service";
import { serverService } from "@/services/server.service";
import { useWebSocket } from "@/hooks/use-websocket";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Send, Users, Loader2, Terminal, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface ConsoleEntry {
  type: "command" | "response" | "error" | "system" | "log";
  content: string;
  timestamp: Date;
}

interface ServerConsoleProps {
  serverId: number;
  isRunning: boolean;
  hasBeenStarted?: boolean;
}

export function ServerConsole({ serverId, isRunning, hasBeenStarted = false }: ServerConsoleProps) {
  const [commandInput, setCommandInput] = useState("");
  const [consoleHistory, setConsoleHistory] = useState<ConsoleEntry[]>([
    {
      type: "system",
      content: isRunning
        ? "Connected to server. Streaming logs..."
        : "Server is not running. Start the server to use the console.",
      timestamp: new Date(),
    },
  ]);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch initial container logs when component mounts (last 500 lines)
  const { data: initialLogs, isLoading: logsLoading } = useQuery({
    queryKey: ["container-logs", serverId],
    queryFn: () => serverService.getServerLogsV2(serverId, 500, "docker", false), // Get last 500 lines
    enabled: isRunning && hasBeenStarted, // Only fetch when running and has been started
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  });

  // Initialize consoleHistory with fetched Minecraft logs
  useEffect(() => {
    if (initialLogs?.logs) {
      const systemMessage: ConsoleEntry = {
        type: "system",
        content: "Connected to server. Streaming logs...",
        timestamp: new Date(),
      };

      const logEntries: ConsoleEntry[] = initialLogs.logs
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.length > 0)
        .map((line) => ({
          type: "log" as const,
          content: line,
          timestamp: new Date(),
        }));

      setConsoleHistory([systemMessage, ...logEntries]);
    }
  }, [initialLogs]);

  // WebSocket for real-time container logs
  const { connected, logLines } = useWebSocket({
    serverId,
    channel: "container_logs", // All container logs
    enabled: isRunning && hasBeenStarted,
    onLogLine: (line) => {
      // Add container log to console
      setConsoleHistory((prev) => [
        ...prev,
        {
          type: "log",
          content: line,
          timestamp: new Date(),
        },
      ]);
    },
  });

  // Get online players
  const { data: players, refetch: refetchPlayers } = useQuery({
    queryKey: ["players", serverId],
    queryFn: () => consoleService.getPlayers(serverId),
    enabled: isRunning,
    refetchInterval: isRunning ? 5000 : false, // Refresh every 5s when running
  });

  // Execute command mutation
  const executeCommand = useMutation({
    mutationFn: (command: string) =>
      consoleService.executeCommand(serverId, command),
    onSuccess: (data) => {
      // Add command to history
      const newEntry: ConsoleEntry = {
        type: "command",
        content: `> ${data.command}`,
        timestamp: new Date(),
      };

      const responseEntry: ConsoleEntry = {
        type: data.success ? "response" : "error",
        content: data.response || "(no output)",
        timestamp: new Date(),
      };

      setConsoleHistory((prev) => [...prev, newEntry, responseEntry]);

      // Refresh player list
      refetchPlayers();
    },
    onError: (error: any) => {
      const errorEntry: ConsoleEntry = {
        type: "error",
        content: error?.response?.data?.detail || "Failed to execute command",
        timestamp: new Date(),
      };

      setConsoleHistory((prev) => [...prev, errorEntry]);
      toast.error("Command failed", {
        description: errorEntry.content,
      });
    },
  });

  // Auto-scroll to bottom when new entries are added
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [consoleHistory]);

  // Handle command submission
  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!commandInput.trim() || !isRunning) return;

    // Add to command history
    setCommandHistory((prev) => [...prev, commandInput]);
    setHistoryIndex(-1);

    // Execute command
    executeCommand.mutate(commandInput);

    // Clear input
    setCommandInput("");
  };

  // Handle keyboard navigation through command history
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (commandHistory.length === 0) return;

      const newIndex =
        historyIndex === -1
          ? commandHistory.length - 1
          : Math.max(0, historyIndex - 1);

      setHistoryIndex(newIndex);
      setCommandInput(commandHistory[newIndex]);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex === -1) return;

      const newIndex = historyIndex + 1;

      if (newIndex >= commandHistory.length) {
        setHistoryIndex(-1);
        setCommandInput("");
      } else {
        setHistoryIndex(newIndex);
        setCommandInput(commandHistory[newIndex]);
      }
    }
  };

  // Format timestamp
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  };

  return (
    <>
      <div className="grid gap-4 lg:grid-cols-4 h-[calc(100vh-20rem)]">
        {/* Console Terminal */}
        <Card className="lg:col-span-3 flex flex-col h-full overflow-hidden py-0">
          {/* Console Header */}
          <div className="flex items-center justify-between px-4 h-12 border-b flex-shrink-0">
            <div className="flex items-center gap-2">
              <Terminal className="size-4 text-muted-foreground" />
              <h3 className="font-semibold">Console</h3>
              {!isRunning && (
                <Badge variant="outline" className="text-xs">
                  Server Offline
                </Badge>
              )}
              {isRunning && connected && (
                <Badge variant="outline" className="text-xs">
                  <span className="size-2 rounded-full bg-green-500 mr-1.5 inline-block" />
                  Live
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConsoleHistory([])}
                disabled={!isRunning}
              >
                Clear
              </Button>
            </div>
          </div>

          {/* Console Output */}
          <div className="flex-1 overflow-hidden">
            <ScrollArea ref={scrollAreaRef} className="h-full">
              <div className="space-y-2 font-mono text-sm p-4">
                {consoleHistory.map((entry, index) => (
                  <div key={index} className="flex gap-2">
                    <span className="text-muted-foreground text-xs w-20 flex-shrink-0">
                      {formatTime(entry.timestamp)}
                    </span>
                    <span
                      className={cn("flex-1 break-all", {
                        "text-blue-600 dark:text-blue-400": entry.type === "command",
                        "text-foreground": entry.type === "response" || entry.type === "log",
                        "text-red-600 dark:text-red-400": entry.type === "error",
                        "text-muted-foreground italic": entry.type === "system",
                      })}
                    >
                      {entry.content}
                    </span>
                  </div>
                ))}
                {executeCommand.isPending && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="size-3 animate-spin" />
                    <span className="text-sm">Executing command...</span>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Console Input */}
          <div className="px-4 py-4 border-t flex-shrink-0">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground font-mono">
                  &gt;
                </span>
                <Input
                  ref={inputRef}
                  type="text"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    isRunning
                      ? "Enter command... (use ↑↓ for history)"
                      : "Server must be running"
                  }
                  disabled={!isRunning || executeCommand.isPending}
                  className="pl-8 font-mono"
                  autoComplete="off"
                />
              </div>
              <Button
                type="submit"
                disabled={!isRunning || !commandInput.trim() || executeCommand.isPending}
              >
                {executeCommand.isPending ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <Send />
                )}
                Send
              </Button>
            </form>
            <p className="text-xs text-muted-foreground mt-2">
              Tip: Use arrow keys to navigate command history
            </p>
          </div>
        </Card>

        {/* Players Sidebar */}
        <Card className="h-full flex flex-col py-0">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="size-4 text-muted-foreground" />
                <h3 className="font-semibold">Players</h3>
              </div>
              <Badge variant="outline">
                {players?.online_players ?? 0} / {players?.max_players ?? 20}
              </Badge>
            </div>
          </div>

          <ScrollArea className="flex-1 p-4">
            {!isRunning ? (
              <div className="flex flex-col items-center justify-center h-full text-center gap-2">
                <AlertCircle className="size-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Server is offline
                </p>
              </div>
            ) : players && players.players.length > 0 ? (
              <div className="space-y-2">
                {players.players.map((playerName, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <Image
                      src={`https://minotar.net/avatar/${encodeURIComponent(playerName)}/32`}
                      alt={playerName}
                      width={32}
                      height={32}
                      className="size-8 rounded-md"
                      unoptimized
                    />
                    <span className="text-sm font-medium">{playerName}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center gap-2">
                <Users className="size-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">No players online</p>
              </div>
            )}
          </ScrollArea>

          <Separator />

          <div className="p-4">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => refetchPlayers()}
              disabled={!isRunning}
            >
              Refresh Players
            </Button>
          </div>
        </Card>
      </div>
    </>
  );
}
