"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import Image from "next/image";
import { consoleService } from "@/services/console.service";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
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
import {
  Users,
  Loader2,
  AlertCircle,
  Crown,
  UserX,
  Ban,
  Shield,
  MessageSquare,
  ShieldOff,
  UserCog,
  RefreshCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface ServerPlayersProps {
  serverId: number;
  isRunning: boolean;
}

export function ServerPlayers({ serverId, isRunning }: ServerPlayersProps) {
  // Player action dialogs
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [kickDialogOpen, setKickDialogOpen] = useState(false);
  const [banDialogOpen, setBanDialogOpen] = useState(false);
  const [messageDialogOpen, setMessageDialogOpen] = useState(false);
  const [confirmOpDialogOpen, setConfirmOpDialogOpen] = useState(false);
  const [kickReason, setKickReason] = useState("");
  const [banReason, setBanReason] = useState("");
  const [privateMessage, setPrivateMessage] = useState("");

  // Get online players
  const { data: players, refetch: refetchPlayers, isLoading } = useQuery({
    queryKey: ["players", serverId],
    queryFn: () => consoleService.getPlayers(serverId),
    enabled: isRunning,
    refetchInterval: isRunning ? 5000 : false, // Refresh every 5s when running
  });

  // Execute command mutation
  const executeCommand = useMutation({
    mutationFn: (command: string) =>
      consoleService.executeCommand(serverId, command),
    onError: (error: any) => {
      toast.error("Command failed", {
        description: error?.response?.data?.detail || "Failed to execute command",
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

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              <Users className="size-6" />
              Online Players
            </h2>
            <p className="text-muted-foreground">
              Manage and interact with players currently online
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-base px-4 py-1.5">
              {players?.online_players ?? 0} / {players?.max_players ?? 20}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchPlayers()}
              disabled={!isRunning || isLoading}
            >
              <RefreshCcw className={cn("size-4", isLoading && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        <Separator />

        {/* Players Grid */}
        {!isRunning ? (
          <Card className="p-12">
            <div className="flex flex-col items-center justify-center text-center gap-3">
              <AlertCircle className="size-12 text-muted-foreground" />
              <div>
                <h3 className="font-semibold text-lg">Server is Offline</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Start the server to see online players
                </p>
              </div>
            </div>
          </Card>
        ) : isLoading ? (
          <Card className="p-12">
            <div className="flex flex-col items-center justify-center text-center gap-3">
              <Loader2 className="size-12 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Loading players...</p>
            </div>
          </Card>
        ) : players && players.players.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
            {players.players.map((playerName, index) => (
              <ContextMenu key={index}>
                <ContextMenuTrigger asChild>
                  <Card
                    className="p-3 hover:border-primary/50 transition-all cursor-pointer group"
                    role="button"
                    tabIndex={0}
                  >
                    <div className="flex flex-col items-center gap-2 text-center">
                      <div className="relative">
                        <Image
                          src={`https://minotar.net/avatar/${encodeURIComponent(playerName)}/48`}
                          alt={playerName}
                          width={48}
                          height={48}
                          className="size-12 rounded-md ring-2 ring-transparent group-hover:ring-primary/20 transition-all"
                          unoptimized
                        />
                        <div className="absolute -bottom-0.5 -right-0.5 size-3 rounded-full bg-green-500 border-2 border-background" />
                      </div>
                      <div className="space-y-0.5 w-full min-w-0">
                        <p className="font-medium text-sm truncate">{playerName}</p>
                        <div className="text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                          Right-click
                        </div>
                      </div>
                    </div>
                  </Card>
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
          <Card className="p-12">
            <div className="flex flex-col items-center justify-center text-center gap-3">
              <Users className="size-12 text-muted-foreground" />
              <div>
                <h3 className="font-semibold text-lg">No Players Online</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  The server is running but no players are connected
                </p>
              </div>
            </div>
          </Card>
        )}
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
