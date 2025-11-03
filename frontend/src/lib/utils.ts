import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format bytes to human readable string
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

/**
 * Format date to localized string
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleString();
}

/**
 * Get status color for server status
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case "running":
      return "text-green-600 dark:text-green-500";
    case "stopped":
      return "text-gray-500 dark:text-gray-400";
    case "starting":
    case "stopping":
      return "text-yellow-600 dark:text-yellow-500";
    case "error":
      return "text-red-600 dark:text-red-500";
    default:
      return "text-gray-500 dark:text-gray-400";
  }
}
