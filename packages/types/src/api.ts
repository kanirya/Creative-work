// API Response wrapper
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  errorMessage?: string;
  correlationId?: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// API Error
export interface ApiError {
  message: string;
  code?: string;
  correlationId?: string;
  timestamp: string;
}
