/**
 * System settings types
 */

export interface SystemSettings {
  id: number;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface SystemSettingsUpdate {
  timezone: string;
}

// List of common timezones
export const TIMEZONES = [
  { value: "Europe/Madrid", label: "Europe/Madrid (GMT+1/+2)" },
  { value: "Europe/London", label: "Europe/London (GMT+0/+1)" },
  { value: "Europe/Paris", label: "Europe/Paris (GMT+1/+2)" },
  { value: "Europe/Berlin", label: "Europe/Berlin (GMT+1/+2)" },
  { value: "Europe/Rome", label: "Europe/Rome (GMT+1/+2)" },
  { value: "Europe/Moscow", label: "Europe/Moscow (GMT+3)" },
  { value: "America/New_York", label: "America/New York (GMT-5/-4)" },
  { value: "America/Chicago", label: "America/Chicago (GMT-6/-5)" },
  { value: "America/Denver", label: "America/Denver (GMT-7/-6)" },
  { value: "America/Los_Angeles", label: "America/Los Angeles (GMT-8/-7)" },
  { value: "America/Mexico_City", label: "America/Mexico City (GMT-6/-5)" },
  { value: "America/Sao_Paulo", label: "America/São Paulo (GMT-3)" },
  { value: "Asia/Tokyo", label: "Asia/Tokyo (GMT+9)" },
  { value: "Asia/Shanghai", label: "Asia/Shanghai (GMT+8)" },
  { value: "Asia/Singapore", label: "Asia/Singapore (GMT+8)" },
  { value: "Asia/Dubai", label: "Asia/Dubai (GMT+4)" },
  { value: "Asia/Kolkata", label: "Asia/Kolkata (GMT+5:30)" },
  { value: "Australia/Sydney", label: "Australia/Sydney (GMT+10/+11)" },
  { value: "Pacific/Auckland", label: "Pacific/Auckland (GMT+12/+13)" },
  { value: "UTC", label: "UTC (GMT+0)" },
] as const;
