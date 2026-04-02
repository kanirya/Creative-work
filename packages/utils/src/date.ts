import { format, formatDistanceToNow, parseISO, isValid } from 'date-fns';

/**
 * Format a date string or Date object to a readable format
 */
export function formatDate(date: string | Date, formatStr: string = 'PPP'): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) {
    return 'Invalid date';
  }
  
  return format(dateObj, formatStr);
}

/**
 * Format a date as relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) {
    return 'Invalid date';
  }
  
  return formatDistanceToNow(dateObj, { addSuffix: true });
}

/**
 * Format a date for display in the UI (e.g., "Jan 15, 2024")
 */
export function formatDisplayDate(date: string | Date): string {
  return formatDate(date, 'MMM d, yyyy');
}

/**
 * Format a date with time (e.g., "Jan 15, 2024 at 3:30 PM")
 */
export function formatDateTime(date: string | Date): string {
  return formatDate(date, 'MMM d, yyyy \'at\' h:mm a');
}

/**
 * Check if a date is in the past
 */
export function isPast(date: string | Date): boolean {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return isValid(dateObj) && dateObj < new Date();
}

/**
 * Check if a date is in the future
 */
export function isFuture(date: string | Date): boolean {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return isValid(dateObj) && dateObj > new Date();
}
