"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Info, AlertCircle } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { PropertyMetadata } from "./property-metadata";

interface PropertyFieldProps {
  metadata: PropertyMetadata;
  value: any;
  onChange: (value: any) => void;
}

export function PropertyField({
  metadata,
  value,
  onChange,
}: PropertyFieldProps) {
  const renderField = () => {
    if (metadata.readOnly) {
      return (
        <Input
          type={metadata.type === "number" ? "number" : "text"}
          value={value ?? ""}
          disabled
          className="bg-muted"
        />
      );
    }

    switch (metadata.type) {
      case "boolean":
        return (
          <div className="flex items-center space-x-2">
            <Switch
              checked={value ?? false}
              onCheckedChange={onChange}
              id={metadata.key}
            />
            <Label htmlFor={metadata.key} className="cursor-pointer">
              {value ? "Enabled" : "Disabled"}
            </Label>
          </div>
        );

      case "number":
        return (
          <Input
            type="number"
            value={value ?? ""}
            onChange={(e) => {
              const val = e.target.value === "" ? undefined : Number(e.target.value);
              onChange(val);
            }}
            min={metadata.min}
            max={metadata.max}
            step={metadata.step ?? 1}
          />
        );

      case "select":
        return (
          <Select
            value={value?.toString() ?? ""}
            onValueChange={(val) => onChange(val)}
          >
            <SelectTrigger>
              <SelectValue placeholder={`Select ${metadata.label.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
              {metadata.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case "string":
      default:
        return (
          <Input
            type="text"
            value={value ?? ""}
            onChange={(e) => onChange(e.target.value)}
            placeholder={metadata.placeholder}
          />
        );
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Label htmlFor={metadata.key} className="text-sm font-medium">
            {metadata.label}
          </Label>
          {metadata.description && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="size-4 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">{metadata.description}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        <div className="flex items-center gap-1">
          {metadata.requiresRestart && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="text-xs">
                    <AlertCircle className="size-3 mr-1" />
                    Restart
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Requires server restart</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          {metadata.requiresWorldRegen && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="text-xs">
                    <AlertCircle className="size-3 mr-1" />
                    World Regen
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Only applies to new worlds or after world regeneration</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          {metadata.readOnly && (
            <Badge variant="secondary" className="text-xs">
              Read-only
            </Badge>
          )}
        </div>
      </div>
      {renderField()}
    </div>
  );
}
