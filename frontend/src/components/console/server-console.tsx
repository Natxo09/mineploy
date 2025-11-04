"use client";

import { useState, useRef, useEffect, useCallback, KeyboardEvent } from "react";
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
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Send, Users, Loader2, Terminal, AlertCircle, ArrowDownToLine, Container, Gamepad2, Lightbulb, Crown, UserX, Ban, Shield, MessageSquare, ShieldOff, UserCog } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { getCommandSuggestions } from "@/lib/minecraft-commands";

type LogCategory = "docker" | "minecraft" | "rcon" | "unknown";

interface ConsoleEntry {
  type: "command" | "response" | "error" | "system" | "log";
  content: string;
  timestamp: Date;
  category?: LogCategory; // For log entries only
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
  const [autoScroll, setAutoScroll] = useState(true);
  const [showDocker, setShowDocker] = useState(true);
  const [showMinecraft, setShowMinecraft] = useState(true);
  const [suggestions, setSuggestions] = useState<Array<{ type: "command" | "player"; text: string; detail: string }>>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Player action dialogs
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [kickDialogOpen, setKickDialogOpen] = useState(false);
  const [banDialogOpen, setBanDialogOpen] = useState(false);
  const [messageDialogOpen, setMessageDialogOpen] = useState(false);
  const [confirmOpDialogOpen, setConfirmOpDialogOpen] = useState(false);
  const [kickReason, setKickReason] = useState("");
  const [banReason, setBanReason] = useState("");
  const [privateMessage, setPrivateMessage] = useState("");

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Categorize log line based on content
  const categorizeLog = useCallback((line: string): LogCategory => {
    // RCON logs (highest priority to detect spam)
    if (line.includes("RCON Listener") || line.includes("RCON Client")) {
      return "rcon";
    }

    // Docker/Init logs
    if (
      line.startsWith("[init]") ||
      line.includes("mc-server-runner") ||
      line.includes("mc-image-helper") ||
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(line) // ISO timestamp
    ) {
      return "docker";
    }

    // Minecraft logs (standard format: [HH:MM:SS] [Thread/LEVEL]:)
    if (/^\[\d{2}:\d{2}:\d{2}\]/.test(line)) {
      return "minecraft";
    }

    return "unknown";
  }, []);

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
          category: categorizeLog(line),
        }));

      setConsoleHistory([systemMessage, ...logEntries]);
    }
  }, [initialLogs, categorizeLog]);

  // WebSocket for real-time container logs
  const { connected, logLines } = useWebSocket({
    serverId,
    channel: "container_logs", // All container logs
    enabled: isRunning && hasBeenStarted,
    onLogLine: (line) => {
      // Add container log to console with category
      setConsoleHistory((prev) => [
        ...prev,
        {
          type: "log",
          content: line,
          timestamp: new Date(),
          category: categorizeLog(line),
        },
      ]);
    },
  });

  // Get online players
  const { data: players, refetch: refetchPlayers } = useQuery({
    queryKey: ["players", serverId],
    queryFn: () => consoleService.getPlayers(serverId),
    enabled: isRunning,
    refetchInterval: isRunning ? 5000 : false, // Refresh every 5s when running (Query Protocol = no log spam)
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

  // Player action handlers
  const handleMakeOp = (playerName: string) => {
    setSelectedPlayer(playerName);
    setConfirmOpDialogOpen(true);
  };

  const confirmMakeOp = () => {
    if (!selectedPlayer) return;
    executeCommand.mutate(`op ${selectedPlayer}`);
    toast.success(`${selectedPlayer} is now an operator`);
    setConfirmOpDialogOpen(false);
    setSelectedPlayer(null);
  };

  const handleRemoveOp = (playerName: string) => {
    executeCommand.mutate(`deop ${playerName}`);
    toast.success(`Removed operator status from ${playerName}`);
  };

  const handleKick = (playerName: string) => {
    setSelectedPlayer(playerName);
    setKickReason("");
    setKickDialogOpen(true);
  };

  const confirmKick = () => {
    if (!selectedPlayer) return;
    const command = kickReason.trim()
      ? `kick ${selectedPlayer} ${kickReason}`
      : `kick ${selectedPlayer}`;
    executeCommand.mutate(command);
    toast.success(`Kicked ${selectedPlayer}`);
    setKickDialogOpen(false);
    setSelectedPlayer(null);
    setKickReason("");
  };

  const handleBan = (playerName: string) => {
    setSelectedPlayer(playerName);
    setBanReason("");
    setBanDialogOpen(true);
  };

  const confirmBan = () => {
    if (!selectedPlayer) return;
    const command = banReason.trim()
      ? `ban ${selectedPlayer} ${banReason}`
      : `ban ${selectedPlayer}`;
    executeCommand.mutate(command);
    toast.success(`Banned ${selectedPlayer}`);
    setBanDialogOpen(false);
    setSelectedPlayer(null);
    setBanReason("");
  };

  const handleWhitelistAdd = (playerName: string) => {
    executeCommand.mutate(`whitelist add ${playerName}`);
    toast.success(`Added ${playerName} to whitelist`);
  };

  const handleWhitelistRemove = (playerName: string) => {
    executeCommand.mutate(`whitelist remove ${playerName}`);
    toast.success(`Removed ${playerName} from whitelist`);
  };

  const handleSendMessage = (playerName: string) => {
    setSelectedPlayer(playerName);
    setPrivateMessage("");
    setMessageDialogOpen(true);
  };

  const confirmSendMessage = () => {
    if (!selectedPlayer || !privateMessage.trim()) return;
    executeCommand.mutate(`tell ${selectedPlayer} ${privateMessage}`);
    toast.success(`Message sent to ${selectedPlayer}`);
    setMessageDialogOpen(false);
    setSelectedPlayer(null);
    setPrivateMessage("");
  };

  // Auto-scroll to bottom when new entries are added (only if enabled)
  useEffect(() => {
    if (autoScroll && scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [consoleHistory, autoScroll]);

  // Update suggestions when command input changes
  useEffect(() => {
    if (!commandInput || !isRunning) {
      setShowSuggestions(false);
      return;
    }

    // Get player names for autocomplete
    const playerNames = players?.players || [];
    const newSuggestions = getCommandSuggestions(commandInput, playerNames);

    setSuggestions(newSuggestions);

    // Set initial selection to first selectable item (skip syntax hints)
    const firstSelectableIndex = newSuggestions.findIndex(
      (s) => s.type !== "syntax" && s.completionText
    );
    setSelectedSuggestion(firstSelectableIndex >= 0 ? firstSelectableIndex : 0);

    setShowSuggestions(newSuggestions.length > 0);
  }, [commandInput, players, isRunning]);

  // Apply a suggestion
  const applySuggestion = (suggestion: typeof suggestions[0]) => {
    // Syntax hints are not selectable
    if (suggestion.type === "syntax" || !suggestion.completionText) {
      return;
    }

    const parts = commandInput.trim().split(/\s+/);

    if (suggestion.type === "command") {
      // Replace first word with command name and add space
      setCommandInput(suggestion.completionText + " ");
    } else if (suggestion.type === "param") {
      // Replace last word with parameter value and add space (more params expected)
      parts[parts.length - 1] = suggestion.completionText;
      setCommandInput(parts.join(" ") + " ");
    } else if (suggestion.type === "player") {
      // Replace last word with player name, NO space (usually last param)
      parts[parts.length - 1] = suggestion.completionText;
      setCommandInput(parts.join(" "));
    }

    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  // Handle command submission
  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!commandInput.trim() || !isRunning) return;

    // Add to command history
    setCommandHistory((prev) => [...prev, commandInput]);
    setHistoryIndex(-1);

    // Execute command
    executeCommand.mutate(commandInput);

    // Clear input and hide suggestions
    setCommandInput("");
    setShowSuggestions(false);
  };

  // Handle keyboard navigation through command history and suggestions
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    // Autocomplete navigation (when suggestions are visible)
    if (showSuggestions && suggestions.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        // Skip syntax hints (non-selectable items)
        let newIndex = selectedSuggestion;
        do {
          newIndex = newIndex < suggestions.length - 1 ? newIndex + 1 : 0;
        } while (
          suggestions[newIndex].type === "syntax" &&
          newIndex !== selectedSuggestion
        );
        setSelectedSuggestion(newIndex);
        return;
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        // Skip syntax hints (non-selectable items)
        let newIndex = selectedSuggestion;
        do {
          newIndex = newIndex > 0 ? newIndex - 1 : suggestions.length - 1;
        } while (
          suggestions[newIndex].type === "syntax" &&
          newIndex !== selectedSuggestion
        );
        setSelectedSuggestion(newIndex);
        return;
      } else if (e.key === "Tab" || e.key === "Enter") {
        if (e.key === "Enter" && !commandInput.trim()) return;

        const currentSuggestion = suggestions[selectedSuggestion];

        // Only apply if it's a selectable suggestion (not syntax hint)
        if (currentSuggestion && currentSuggestion.type !== "syntax" && currentSuggestion.completionText) {
          if (e.key === "Tab") {
            e.preventDefault();
            applySuggestion(currentSuggestion);
            return;
          }

          // Enter with suggestion selected - apply it
          if (selectedSuggestion >= 0 && selectedSuggestion < suggestions.length) {
            e.preventDefault();
            applySuggestion(currentSuggestion);
            return;
          }
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        setShowSuggestions(false);
        return;
      }
    }

    // Command history navigation (when no suggestions or different keys)
    if (e.key === "ArrowUp" && !showSuggestions) {
      e.preventDefault();
      if (commandHistory.length === 0) return;

      const newIndex =
        historyIndex === -1
          ? commandHistory.length - 1
          : Math.max(0, historyIndex - 1);

      setHistoryIndex(newIndex);
      setCommandInput(commandHistory[newIndex]);
    } else if (e.key === "ArrowDown" && !showSuggestions) {
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

  // Filter console history based on selected filters
  const filteredHistory = consoleHistory.filter((entry) => {
    // Always show non-log entries (commands, errors, system messages)
    if (entry.type !== "log") return true;

    // Filter logs by category
    const category = entry.category || "unknown";
    if (category === "docker" && !showDocker) return false;
    if (category === "minecraft" && !showMinecraft) return false;
    // RCON logs are filtered in the backend, so they shouldn't appear here

    return true;
  });

  // Get color class for log based on category
  const getLogColorClass = (category?: LogCategory): string => {
    switch (category) {
      case "docker":
        return "text-purple-600 dark:text-purple-400";
      case "minecraft":
        return "text-green-600 dark:text-green-400";
      case "rcon":
        return "text-orange-600 dark:text-orange-400";
      default:
        return "text-foreground";
    }
  };

  return (
    <>
      <div className="grid gap-4 lg:grid-cols-4 h-[calc(100vh-20rem)]">
        {/* Console Terminal */}
        <Card className="lg:col-span-3 flex flex-col h-full overflow-hidden py-0">
          {/* Console Header */}
          <div className="border-b flex-shrink-0">
            {/* Top row */}
            <div className="flex items-center justify-between px-4 h-12">
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
                  variant={autoScroll ? "default" : "outline"}
                  size="sm"
                  onClick={() => setAutoScroll(!autoScroll)}
                  className="gap-2"
                >
                  <ArrowDownToLine className="size-4" />
                  Auto-scroll
                </Button>
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

            {/* Filters row */}
            <div className="flex items-center gap-2 px-4 pb-2">
              <span className="text-xs text-muted-foreground">Filters:</span>
              <Button
                variant={showDocker ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setShowDocker(!showDocker)}
                className="h-7 gap-1.5 text-xs"
              >
                <Container className="size-3" />
                Docker
              </Button>
              <Button
                variant={showMinecraft ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setShowMinecraft(!showMinecraft)}
                className="h-7 gap-1.5 text-xs"
              >
                <Gamepad2 className="size-3" />
                Minecraft
              </Button>
            </div>
          </div>

          {/* Console Output */}
          <div className="flex-1 overflow-hidden">
            <ScrollArea ref={scrollAreaRef} className="h-full">
              <div className="space-y-2 font-mono text-sm p-4">
                {filteredHistory.map((entry, index) => (
                  <div key={index} className="flex gap-2">
                    <span className="text-muted-foreground text-xs w-20 flex-shrink-0">
                      {formatTime(entry.timestamp)}
                    </span>
                    <span
                      className={cn("flex-1 break-all", {
                        "text-blue-600 dark:text-blue-400": entry.type === "command",
                        "text-red-600 dark:text-red-400": entry.type === "error",
                        "text-muted-foreground italic": entry.type === "system",
                        "text-foreground": entry.type === "response",
                        // Apply color based on log category
                        [getLogColorClass(entry.category)]: entry.type === "log",
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
                {/* Autocomplete suggestions dropdown */}
                {showSuggestions && suggestions.length > 0 && (
                  <div
                    ref={suggestionsRef}
                    className="absolute bottom-full left-0 right-0 mb-2 bg-popover border rounded-md shadow-lg max-h-64 overflow-auto z-50"
                  >
                    {suggestions.map((suggestion, index) => {
                      const isSyntaxHint = suggestion.type === "syntax";
                      const isSelectable = !isSyntaxHint && suggestion.completionText;

                      return (
                        <div
                          key={index}
                          className={cn(
                            "px-3 py-2 border-b last:border-b-0 transition-colors",
                            {
                              "cursor-pointer hover:bg-accent": isSelectable,
                              "bg-accent": index === selectedSuggestion && isSelectable,
                              "bg-muted/50 cursor-default": isSyntaxHint,
                            }
                          )}
                          onClick={() => isSelectable && applySuggestion(suggestion)}
                          onMouseEnter={() => isSelectable && setSelectedSuggestion(index)}
                        >
                          <div className="flex items-start gap-2">
                            <Lightbulb className={cn(
                              "size-4 mt-0.5 flex-shrink-0",
                              isSyntaxHint ? "text-yellow-500" : "text-muted-foreground"
                            )} />
                            <div className="flex-1 min-w-0">
                              <div className={cn(
                                "font-mono text-sm font-medium truncate",
                                isSyntaxHint && "text-muted-foreground italic"
                              )}>
                                {suggestion.text}
                              </div>
                              <div className="text-xs text-muted-foreground truncate">
                                {suggestion.detail}
                              </div>
                            </div>
                            {suggestion.type === "player" && (
                              <Badge variant="outline" className="text-xs flex-shrink-0">
                                Player
                              </Badge>
                            )}
                            {suggestion.type === "param" && (
                              <Badge variant="secondary" className="text-xs flex-shrink-0">
                                Param
                              </Badge>
                            )}
                            {isSyntaxHint && (
                              <Badge variant="outline" className="text-xs flex-shrink-0">
                                Syntax
                              </Badge>
                            )}
                          </div>
                        </div>
                      );
                    })}
                    <div className="px-3 py-1.5 bg-muted/50 text-xs text-muted-foreground border-t">
                      <kbd className="px-1.5 py-0.5 bg-background border rounded text-xs">Tab</kbd> or{" "}
                      <kbd className="px-1.5 py-0.5 bg-background border rounded text-xs">Enter</kbd> to select •{" "}
                      <kbd className="px-1.5 py-0.5 bg-background border rounded text-xs">↑↓</kbd> to navigate •{" "}
                      <kbd className="px-1.5 py-0.5 bg-background border rounded text-xs">Esc</kbd> to close
                    </div>
                  </div>
                )}

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
                      ? "Enter command... (Tab for autocomplete)"
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
              Tip: Press Tab for command suggestions, ↑↓ to navigate history
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
                  <ContextMenu key={index}>
                    <ContextMenuTrigger>
                      <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 transition-colors cursor-context-menu">
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
                    </ContextMenuTrigger>
                    <ContextMenuContent>
                      <ContextMenuItem onClick={() => handleMakeOp(playerName)}>
                        <Crown className="size-4 mr-2" />
                        Make Operator
                      </ContextMenuItem>
                      <ContextMenuItem onClick={() => handleRemoveOp(playerName)}>
                        <UserCog className="size-4 mr-2" />
                        Remove Operator
                      </ContextMenuItem>
                      <ContextMenuSeparator />
                      <ContextMenuItem onClick={() => handleKick(playerName)}>
                        <UserX className="size-4 mr-2" />
                        Kick Player
                      </ContextMenuItem>
                      <ContextMenuItem
                        className="text-destructive focus:text-destructive"
                        onClick={() => handleBan(playerName)}
                      >
                        <Ban className="size-4 mr-2" />
                        Ban Player
                      </ContextMenuItem>
                      <ContextMenuSeparator />
                      <ContextMenuItem onClick={() => handleWhitelistAdd(playerName)}>
                        <Shield className="size-4 mr-2" />
                        Add to Whitelist
                      </ContextMenuItem>
                      <ContextMenuItem onClick={() => handleWhitelistRemove(playerName)}>
                        <ShieldOff className="size-4 mr-2" />
                        Remove from Whitelist
                      </ContextMenuItem>
                      <ContextMenuSeparator />
                      <ContextMenuItem onClick={() => handleSendMessage(playerName)}>
                        <MessageSquare className="size-4 mr-2" />
                        Send Private Message
                      </ContextMenuItem>
                    </ContextMenuContent>
                  </ContextMenu>
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

      {/* Kick Dialog */}
      <Dialog open={kickDialogOpen} onOpenChange={setKickDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Kick Player</DialogTitle>
            <DialogDescription>
              Kick {selectedPlayer} from the server. You can optionally provide a reason.
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="Reason (optional)"
            value={kickReason}
            onChange={(e) => setKickReason(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") confirmKick();
            }}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setKickDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={confirmKick}>Kick Player</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Ban Dialog */}
      <Dialog open={banDialogOpen} onOpenChange={setBanDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ban Player</DialogTitle>
            <DialogDescription>
              Permanently ban {selectedPlayer} from the server. You can optionally provide a reason.
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="Reason (optional)"
            value={banReason}
            onChange={(e) => setBanReason(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") confirmBan();
            }}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setBanDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmBan}>
              Ban Player
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Send Message Dialog */}
      <Dialog open={messageDialogOpen} onOpenChange={setMessageDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Private Message</DialogTitle>
            <DialogDescription>
              Send a private message to {selectedPlayer}.
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="Type your message..."
            value={privateMessage}
            onChange={(e) => setPrivateMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") confirmSendMessage();
            }}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setMessageDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={confirmSendMessage} disabled={!privateMessage.trim()}>
              Send Message
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* OP Confirmation Dialog */}
      <AlertDialog open={confirmOpDialogOpen} onOpenChange={setConfirmOpDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Make Operator</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to make {selectedPlayer} a server operator?
              Operators have full control over the server.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmMakeOp}>
              Make Operator
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
