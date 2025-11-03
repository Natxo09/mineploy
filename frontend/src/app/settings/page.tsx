"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsService } from "@/services/settings.service";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Settings as SettingsIcon,
  Clock,
  Save,
  Loader2,
  AlertCircle,
  Info,
  Globe,
} from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";
import { TIMEZONES } from "@/types/settings";
import { formatDateTime, getTimezoneName } from "@/lib/date-utils";
import { useAuthStore } from "@/stores/auth.store";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const isAdmin = user?.role === "admin";

  // Fetch current settings
  const {
    data: settings,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["system-settings"],
    queryFn: () => settingsService.getSettings(),
  });

  const [selectedTimezone, setSelectedTimezone] = useState<string | null>(null);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: settingsService.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system-settings"] });
      toast.success("Settings updated successfully", {
        description: "The system timezone has been updated.",
      });
      setSelectedTimezone(null);
    },
    onError: (error: any) => {
      toast.error("Failed to update settings", {
        description: error?.message || "An error occurred while updating settings.",
      });
    },
  });

  const handleSave = () => {
    if (!selectedTimezone) return;
    updateMutation.mutate({ timezone: selectedTimezone });
  };

  const hasChanges = selectedTimezone && selectedTimezone !== settings?.timezone;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2">
        <AlertCircle className="size-8 text-destructive" />
        <p className="text-sm text-muted-foreground">Failed to load settings</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <SettingsIcon className="size-8" />
            Settings
          </h1>
          <p className="text-muted-foreground">
            Manage system-wide configuration and preferences
          </p>
        </div>
      </div>

      <Separator />

      {/* Admin Only Warning */}
      {!isAdmin && (
        <Alert>
          <Info className="size-4" />
          <AlertTitle>View Only</AlertTitle>
          <AlertDescription>
            You need administrator privileges to modify system settings.
          </AlertDescription>
        </Alert>
      )}

      {/* Timezone Settings */}
      <Card className="p-6">
        <div className="space-y-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Clock className="size-5 text-muted-foreground" />
                <h2 className="text-xl font-semibold">Timezone Configuration</h2>
              </div>
              <p className="text-sm text-muted-foreground">
                Configure the system timezone for displaying dates and times across the
                application
              </p>
            </div>
            {settings?.updated_at && (
              <Badge variant="outline" className="ml-4 flex-shrink-0">
                Last updated: {formatDateTime(settings.updated_at)}
              </Badge>
            )}
          </div>

          <Separator />

          <div className="grid gap-6 md:grid-cols-2">
            {/* Current Timezone */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="timezone">System Timezone</Label>
                <Select
                  value={selectedTimezone || settings?.timezone}
                  onValueChange={setSelectedTimezone}
                  disabled={!isAdmin}
                >
                  <SelectTrigger id="timezone">
                    <SelectValue placeholder="Select timezone..." />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEZONES.map((tz) => (
                      <SelectItem key={tz.value} value={tz.value}>
                        {tz.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  This timezone will be used to display dates and times throughout the
                  application
                </p>
              </div>

              {hasChanges && (
                <div className="flex gap-2">
                  <Button
                    onClick={handleSave}
                    disabled={updateMutation.isPending}
                    className="flex-1"
                  >
                    {updateMutation.isPending ? (
                      <>
                        <Loader2 className="size-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="size-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setSelectedTimezone(null)}
                    disabled={updateMutation.isPending}
                  >
                    Cancel
                  </Button>
                </div>
              )}
            </div>

            {/* Info Panel */}
            <div className="space-y-4">
              <Card className="bg-muted/50 border-muted p-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Globe className="size-4 text-muted-foreground" />
                    <span className="text-sm font-semibold">Timezone Information</span>
                  </div>
                  <Separator />
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Current System:</span>
                      <span className="font-medium">{settings?.timezone}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Your Browser:</span>
                      <span className="font-medium">{getTimezoneName()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Current Time:</span>
                      <span className="font-medium">
                        {formatDateTime(new Date().toISOString())}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>

              <Alert>
                <Info className="size-4" />
                <AlertDescription className="text-xs">
                  Changing the timezone will affect how dates and times are displayed in
                  logs, statistics, and other parts of the application. Existing data will
                  be converted to the new timezone automatically.
                </AlertDescription>
              </Alert>
            </div>
          </div>
        </div>
      </Card>

      {/* Future Settings Sections */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <SettingsIcon className="size-5 text-muted-foreground" />
            <h2 className="text-xl font-semibold">Additional Settings</h2>
          </div>
          <Separator />
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">
              More configuration options will be available here in future updates
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
