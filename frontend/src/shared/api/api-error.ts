import type { AxiosError } from "axios";

import type { ApiErrorBody } from "./types";

export function extractApiError(error: unknown, fallback: string): string {
  const axiosError = error as AxiosError<ApiErrorBody>;
  return axiosError.response?.data?.error ?? axiosError.response?.data?.message ?? fallback;
}
