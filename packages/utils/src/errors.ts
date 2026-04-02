/**
 * Format error message for display to users
 */
export function formatErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unexpected error occurred';
}

/**
 * Extract error details from API error response
 */
export function extractApiError(error: any): { message: string; code?: string } {
  if (error?.response?.data?.message) {
    return {
      message: error.response.data.message,
      code: error.response.data.code,
    };
  }
  
  if (error?.message) {
    return { message: error.message };
  }
  
  return { message: 'An unexpected error occurred' };
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: any): boolean {
  return (
    error?.code === 'ECONNREFUSED' ||
    error?.code === 'ENOTFOUND' ||
    error?.code === 'ETIMEDOUT' ||
    error?.message?.includes('Network Error') ||
    error?.message?.includes('network')
  );
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error: any): boolean {
  return (
    error?.response?.status === 401 ||
    error?.response?.status === 403 ||
    error?.code === 'UNAUTHORIZED'
  );
}

/**
 * Create user-friendly error message based on error type
 */
export function getUserFriendlyError(error: unknown): string {
  if (isNetworkError(error)) {
    return 'Unable to connect to the server. Please check your internet connection.';
  }
  
  if (isAuthError(error)) {
    return 'Your session has expired. Please log in again.';
  }
  
  return formatErrorMessage(error);
}
