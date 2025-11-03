/**
 * Date and time utility functions
 */

/**
 * Format a date string to local date and time
 * @param dateString - ISO date string to format
 * @param options - Optional Intl.DateTimeFormatOptions
 * @param timezone - Optional IANA timezone (e.g., "Europe/Madrid", "America/New_York")
 */
export function formatDateTime(
  dateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions,
  timezone?: string
): string {
  if (!dateString) return "Never";

  const date = new Date(dateString);

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    ...(timezone && { timeZone: timezone }),
    ...options,
  };

  return date.toLocaleString(undefined, defaultOptions);
}

/**
 * Format a date string to local date only
 * @param dateString - ISO date string to format
 * @param options - Optional Intl.DateTimeFormatOptions
 * @param timezone - Optional IANA timezone (e.g., "Europe/Madrid", "America/New_York")
 */
export function formatDate(
  dateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions,
  timezone?: string
): string {
  if (!dateString) return "Never";

  const date = new Date(dateString);

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    ...(timezone && { timeZone: timezone }),
    ...options,
  };

  return date.toLocaleDateString(undefined, defaultOptions);
}

/**
 * Format a date string to local time only
 * @param dateString - ISO date string to format
 * @param options - Optional Intl.DateTimeFormatOptions
 * @param timezone - Optional IANA timezone (e.g., "Europe/Madrid", "America/New_York")
 */
export function formatTime(
  dateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions,
  timezone?: string
): string {
  if (!dateString) return "Never";

  const date = new Date(dateString);

  const defaultOptions: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    ...(timezone && { timeZone: timezone }),
    ...options,
  };

  return date.toLocaleTimeString(undefined, defaultOptions);
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return "Never";

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) {
    return "Just now";
  } else if (diffMins < 60) {
    return `${diffMins} ${diffMins === 1 ? "minute" : "minutes"} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? "hour" : "hours"} ago`;
  } else if (diffDays < 30) {
    return `${diffDays} ${diffDays === 1 ? "day" : "days"} ago`;
  } else {
    return formatDate(dateString);
  }
}

/**
 * Get current timezone name
 */
export function getTimezoneName(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

/**
 * Get timezone offset in hours
 */
export function getTimezoneOffset(): number {
  return -new Date().getTimezoneOffset() / 60;
}
