"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { propertiesService } from "@/services/properties.service";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Accordion } from "@/components/ui/accordion";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Save, RotateCcw, AlertTriangle, Info } from "lucide-react";
import { toast } from "sonner";
import type {
  ServerProperties,
  UpdateServerPropertiesRequest,
} from "@/types";
import { PropertySection } from "./property-section";
import { PROPERTY_METADATA } from "./property-metadata";

interface ServerSettingsProps {
  serverId: number;
  isRunning: boolean;
}

export function ServerSettings({ serverId, isRunning }: ServerSettingsProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<ServerProperties>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Fetch current properties
  const {
    data: properties,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["server-properties", serverId],
    queryFn: () => propertiesService.getProperties(serverId),
  });

  // Initialize form data when properties load
  useEffect(() => {
    if (properties) {
      setFormData(properties);
    }
  }, [properties]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdateServerPropertiesRequest) =>
      propertiesService.updateProperties(serverId, data),
    onSuccess: (updatedProperties) => {
      queryClient.setQueryData(
        ["server-properties", serverId],
        updatedProperties
      );
      setFormData(updatedProperties);
      setHasChanges(false);
      toast.success("Server properties updated successfully", {
        description: isRunning
          ? "Restart the server for changes to take effect"
          : undefined,
      });
    },
    onError: (error: any) => {
      toast.error("Failed to update properties", {
        description: error.response?.data?.detail || error.message,
      });
    },
  });

  const handleFieldChange = (key: keyof ServerProperties, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    if (!properties) return;

    // Calculate only changed fields
    const changes: UpdateServerPropertiesRequest = {};
    Object.keys(formData).forEach((key) => {
      const typedKey = key as keyof ServerProperties;
      if (formData[typedKey] !== properties[typedKey]) {
        (changes as any)[typedKey] = formData[typedKey];
      }
    });

    if (Object.keys(changes).length === 0) {
      toast.info("No changes to save");
      return;
    }

    updateMutation.mutate(changes);
  };

  const handleReset = () => {
    if (properties) {
      setFormData(properties);
      setHasChanges(false);
      toast.info("Changes discarded");
    }
  };

  if (isLoading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="size-4" />
        <AlertDescription>
          Failed to load server properties. Make sure the server has been started at
          least once.
        </AlertDescription>
      </Alert>
    );
  }

  if (!properties) {
    return null;
  }

  // Group metadata by category
  const categorizedMetadata = PROPERTY_METADATA.reduce(
    (acc, meta) => {
      if (!acc[meta.category]) {
        acc[meta.category] = [];
      }
      acc[meta.category].push(meta);
      return acc;
    },
    {} as Record<string, typeof PROPERTY_METADATA>
  );

  return (
    <div className="space-y-4">
      {/* Info Banner */}
      {isRunning && (
        <Alert>
          <Info className="size-4" />
          <AlertDescription>
            Some property changes require a server restart to take effect.
          </AlertDescription>
        </Alert>
      )}

      {/* Properties Form */}
      <Card className="p-6">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold">Server Properties</h3>
            <p className="text-sm text-muted-foreground">
              Configure your Minecraft server settings
            </p>
          </div>

          <Separator />

          <Accordion type="multiple" defaultValue={["Server", "Gameplay"]} className="w-full">
            {Object.entries(categorizedMetadata).map(([category, metadata]) => (
              <PropertySection
                key={category}
                category={category}
                metadata={metadata}
                formData={formData}
                onChange={handleFieldChange}
              />
            ))}
          </Accordion>
        </div>
      </Card>

      {/* Action Buttons */}
      {hasChanges && (
        <div className="flex items-center justify-between gap-4 p-4 border rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground">
            You have unsaved changes
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleReset}
              disabled={updateMutation.isPending}
            >
              <RotateCcw className="size-4" />
              Discard
            </Button>
            <Button onClick={handleSave} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Save className="size-4" />
              )}
              Save Changes
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
