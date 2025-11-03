"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { useServerActions } from "@/hooks/use-servers";
import { useWebSocket } from "@/hooks/use-websocket";
import { ServerLogsViewer } from "@/components/servers/server-logs-viewer";
import { ServerType, ServerStatus } from "@/types";
import { Loader2, CheckCircle2 } from "lucide-react";

interface CreateServerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const serverTypes = [
  { value: ServerType.VANILLA, label: "Vanilla", description: "Official Minecraft server" },
  { value: ServerType.PAPER, label: "Paper", description: "High performance fork of Spigot" },
  { value: ServerType.SPIGOT, label: "Spigot", description: "Modified Minecraft server with plugins" },
  { value: ServerType.FABRIC, label: "Fabric", description: "Lightweight modding framework" },
  { value: ServerType.FORGE, label: "Forge", description: "Popular modding platform" },
  { value: ServerType.NEOFORGE, label: "NeoForge", description: "Modern fork of Forge" },
  { value: ServerType.PURPUR, label: "Purpur", description: "Feature-rich Paper fork" },
];

export function CreateServerDialog({ open, onOpenChange }: CreateServerDialogProps) {
  const { createServer } = useServerActions();
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    server_type: ServerType.PAPER,
    version: "1.20.4",
    memory_mb: 2048,
    port: "",
    rcon_port: "",
  });
  const [memoryUnit, setMemoryUnit] = useState<"MB" | "GB">("GB");
  const [errors, setErrors] = useState<Record<string, string>>({});

  // State for showing logs during creation
  const [showLogs, setShowLogs] = useState(false);
  const [createdServerId, setCreatedServerId] = useState<number | null>(null);
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null);

  // WebSocket for real-time logs
  // Only connect if server is downloading or initializing (not stopped)
  const shouldConnect = showLogs &&
    createdServerId !== null &&
    serverStatus !== ServerStatus.STOPPED;

  const { logs, connected, clearLogs, disconnect } = useWebSocket({
    serverId: createdServerId!,
    enabled: shouldConnect,
    onStatusUpdate: (status) => {
      setServerStatus(status as ServerStatus);
    },
  });

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Server name is required";
    } else if (formData.name.length > 100) {
      newErrors.name = "Server name must be less than 100 characters";
    }

    if (!formData.version.trim()) {
      newErrors.version = "Version is required";
    } else if (formData.version.length > 20) {
      newErrors.version = "Version must be less than 20 characters";
    }

    if (formData.port && (parseInt(formData.port) < 1024 || parseInt(formData.port) > 65535)) {
      newErrors.port = "Port must be between 1024 and 65535";
    }

    if (formData.rcon_port && (parseInt(formData.rcon_port) < 1024 || parseInt(formData.rcon_port) > 65535)) {
      newErrors.rcon_port = "RCON port must be between 1024 and 65535";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const payload = {
      name: formData.name.trim(),
      description: formData.description.trim() || undefined,
      server_type: formData.server_type,
      version: formData.version.trim(),
      memory_mb: formData.memory_mb,
      port: formData.port ? parseInt(formData.port) : undefined,
      rcon_port: formData.rcon_port ? parseInt(formData.rcon_port) : undefined,
    };

    createServer.mutate(payload, {
      onSuccess: (data) => {
        // Show logs viewer only if server is downloading/initializing
        setCreatedServerId(data.id);
        setServerStatus(data.status);

        // Only show logs if server is in a transitional state
        if (data.status === ServerStatus.DOWNLOADING || data.status === ServerStatus.INITIALIZING) {
          setShowLogs(true);
        } else {
          // Server is already stopped (created successfully), close dialog
          setTimeout(() => handleClose(), 500);
        }
      },
    });
  };

  const handleReset = () => {
    setFormData({
      name: "",
      description: "",
      server_type: ServerType.PAPER,
      version: "1.20.4",
      memory_mb: 2048,
      port: "",
      rcon_port: "",
    });
    setMemoryUnit("GB");
    setErrors({});
  };

  const handleClose = () => {
    disconnect();
    clearLogs();
    setShowLogs(false);
    setCreatedServerId(null);
    setServerStatus(null);
    handleReset();
    onOpenChange(false);
  };

  // Auto-close when server creation is complete
  useEffect(() => {
    if (serverStatus === ServerStatus.STOPPED && createdServerId !== null) {
      // Close immediately when server creation is complete (STOPPED state)
      // Don't show logs for stopped servers - they're not running yet
      handleClose();
    }
  }, [serverStatus, createdServerId]);

  return (
    <Dialog open={open} onOpenChange={showLogs ? undefined : onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{showLogs ? "Creating Server..." : "Create New Server"}</DialogTitle>
          <DialogDescription>
            {showLogs
              ? "Please wait while we download the Docker image and create your server. This may take several minutes on the first run."
              : "Configure your new Minecraft server. Ports will be automatically assigned if not specified."}
          </DialogDescription>
        </DialogHeader>

        {showLogs ? (
          /* Show logs viewer during creation */
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {serverStatus === ServerStatus.DOWNLOADING && (
                  <>
                    <Loader2 className="size-4 animate-spin text-orange-500" />
                    <span className="text-sm font-medium">Downloading Docker image...</span>
                  </>
                )}
                {serverStatus === ServerStatus.INITIALIZING && (
                  <>
                    <Loader2 className="size-4 animate-spin text-orange-500" />
                    <span className="text-sm font-medium">Initializing container...</span>
                  </>
                )}
                {serverStatus === ServerStatus.STOPPED && (
                  <>
                    <CheckCircle2 className="size-4 text-green-500" />
                    <span className="text-sm font-medium text-green-600">Server created successfully!</span>
                  </>
                )}
              </div>
              {connected && <span className="text-xs text-muted-foreground">Connected</span>}
            </div>

            <ServerLogsViewer logs={logs} />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={serverStatus !== ServerStatus.STOPPED}
              >
                {serverStatus === ServerStatus.STOPPED ? "Close" : "Creating..."}
              </Button>
            </DialogFooter>
          </div>
        ) : (
          /* Show form for configuration */
          <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Basic Information</h3>

            {/* Server Name */}
            <div className="space-y-2">
              <Label htmlFor="name">
                Server Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                placeholder="My Survival Server"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className={errors.name ? "border-destructive" : ""}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                placeholder="A brief description of your server..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>
          </div>

          <Separator />

          {/* Server Configuration */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Server Configuration</h3>

            {/* Server Type */}
            <div className="space-y-2">
              <Label htmlFor="server_type">
                Server Type <span className="text-destructive">*</span>
              </Label>
              <Select
                value={formData.server_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, server_type: value as ServerType })
                }
              >
                <SelectTrigger id="server_type">
                  <SelectValue>
                    {serverTypes.find(t => t.value === formData.server_type)?.label}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {serverTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex flex-col py-1">
                        <span className="font-medium">{type.label}</span>
                        <span className="text-xs text-muted-foreground">
                          {type.description}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Version */}
            <div className="space-y-2">
              <Label htmlFor="version">
                Version <span className="text-destructive">*</span>
              </Label>
              <Input
                id="version"
                placeholder="1.20.4"
                value={formData.version}
                onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                className={errors.version ? "border-destructive" : ""}
              />
              {errors.version && (
                <p className="text-sm text-destructive">{errors.version}</p>
              )}
            </div>
          </div>

          <Separator />

          {/* Resources */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Resources</h3>

            {/* Memory Allocation */}
            <div className="space-y-2">
              <Label>Memory Allocation</Label>
              <div className="flex items-center gap-4">
                <div className="flex-1 space-y-2">
                  <Slider
                    min={512}
                    max={131072}
                    step={512}
                    value={[formData.memory_mb]}
                    onValueChange={(value) =>
                      setFormData({ ...formData, memory_mb: value[0] })
                    }
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>512 MB</span>
                    <span>128 GB</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min={memoryUnit === "MB" ? 512 : 0.5}
                    max={memoryUnit === "MB" ? 131072 : 128}
                    step={memoryUnit === "MB" ? 512 : 0.5}
                    value={
                      memoryUnit === "MB"
                        ? formData.memory_mb
                        : +(formData.memory_mb / 1024).toFixed(1)
                    }
                    onChange={(e) => {
                      const value = parseFloat(e.target.value);
                      if (!isNaN(value)) {
                        const mb = memoryUnit === "MB" ? value : Math.round(value * 1024);
                        if (mb >= 512 && mb <= 131072) {
                          setFormData({ ...formData, memory_mb: mb });
                        }
                      }
                    }}
                    className="w-24 text-right"
                  />
                  <Select value={memoryUnit} onValueChange={(v) => setMemoryUnit(v as "MB" | "GB")}>
                    <SelectTrigger className="w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="MB">MB</SelectItem>
                      <SelectItem value="GB">GB</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </div>

          <Separator />

          {/* Network Configuration */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">Network Configuration</h3>
              <span className="text-xs text-muted-foreground">
                Optional - auto-assigned if empty
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="port">Server Port</Label>
                <Input
                  id="port"
                  type="number"
                  placeholder="Auto (25565-25664)"
                  value={formData.port}
                  onChange={(e) => setFormData({ ...formData, port: e.target.value })}
                  className={errors.port ? "border-destructive" : ""}
                />
                {errors.port && (
                  <p className="text-sm text-destructive">{errors.port}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="rcon_port">RCON Port</Label>
                <Input
                  id="rcon_port"
                  type="number"
                  placeholder="Auto (35565-35664)"
                  value={formData.rcon_port}
                  onChange={(e) => setFormData({ ...formData, rcon_port: e.target.value })}
                  className={errors.rcon_port ? "border-destructive" : ""}
                />
                {errors.rcon_port && (
                  <p className="text-sm text-destructive">{errors.rcon_port}</p>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                handleReset();
                onOpenChange(false);
              }}
              disabled={createServer.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createServer.isPending}>
              {createServer.isPending ? (
                <>
                  <Loader2 className="animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Server"
              )}
            </Button>
          </DialogFooter>
        </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
