export interface ApiErrorBody {
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
}
