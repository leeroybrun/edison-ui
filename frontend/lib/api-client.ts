/**
 * Frontend API Client for Edison UI.
 *
 * Provides a type-safe, consistent API client with:
 * - Automatic error handling and typed errors
 * - Loading/error/stale state management
 * - Request cancellation via AbortController
 * - Retry with exponential backoff for 5xx errors
 * - Authorization token support for remote access
 */

/** Guard failure detail from API. */
export interface GuardFailure {
  guard: string;
  reason: string;
}

/** Validation error detail from API. */
export interface ValidationDetail {
  field: string;
  message: string;
}

/** API error response structure. */
export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: ValidationDetail[];
  guardFailures?: GuardFailure[];
  correlationId?: string;
}

/** Custom error class for API errors. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly errorCode: string,
    message: string,
    public readonly details?: ValidationDetail[],
    public readonly guardFailures?: GuardFailure[],
    public readonly correlationId?: string,
  ) {
    super(message);
    this.name = "ApiError";
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/** Custom error class for network errors. */
export class NetworkError extends Error {
  constructor(
    message: string,
    public readonly cause?: Error,
  ) {
    super(message);
    this.name = "NetworkError";
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

/** API response wrapper with metadata. */
export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

/** Request options for GET requests. */
export interface GetRequestOptions {
  params?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
}

/** Request options for mutation requests. */
export interface MutationRequestOptions {
  body?: unknown;
  signal?: AbortSignal;
}

/** API client configuration. */
export interface ApiClientConfig {
  baseUrl?: string;
  token?: string;
  retries?: number;
  retryDelay?: number;
}

/** API client instance. */
export interface ApiClient {
  readonly baseUrl: string;
  readonly token?: string;

  get<T>(path: string, options?: GetRequestOptions): Promise<ApiResponse<T>>;
  post<T>(
    path: string,
    options?: MutationRequestOptions,
  ): Promise<ApiResponse<T>>;
  patch<T>(
    path: string,
    options?: MutationRequestOptions,
  ): Promise<ApiResponse<T>>;
  delete<T>(
    path: string,
    options?: MutationRequestOptions,
  ): Promise<ApiResponse<T>>;
}

const DEFAULT_BASE_URL = "http://localhost:8000/api/v1";
const DEFAULT_RETRIES = 0;
const DEFAULT_RETRY_DELAY = 1000;

/**
 * Create an API client instance.
 *
 * @param config - Optional configuration
 * @returns API client instance
 */
export function createApiClient(config: ApiClientConfig = {}): ApiClient {
  const baseUrl = config.baseUrl ?? DEFAULT_BASE_URL;
  const token = config.token;
  const maxRetries = config.retries ?? DEFAULT_RETRIES;
  const baseRetryDelay = config.retryDelay ?? DEFAULT_RETRY_DELAY;

  function buildUrl(
    path: string,
    params?: Record<string, string | number | boolean | undefined>,
  ): string {
    const url = new URL(
      path.startsWith("/") ? path.slice(1) : path,
      baseUrl + "/",
    );

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.set(key, String(value));
        }
      });
    }

    return url.toString();
  }

  function buildHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

  async function parseErrorResponse(
    response: Response,
  ): Promise<ApiErrorResponse> {
    try {
      return await response.json();
    } catch {
      return {
        error: "unknown_error",
        message: `HTTP ${response.status}`,
      };
    }
  }

  async function handleResponse<T>(
    response: Response,
  ): Promise<ApiResponse<T>> {
    if (!response.ok) {
      const errorData = await parseErrorResponse(response);
      throw new ApiError(
        response.status,
        errorData.error,
        errorData.message,
        errorData.details,
        errorData.guardFailures,
        errorData.correlationId,
      );
    }

    let data: T;
    try {
      data = await response.json();
    } catch {
      data = null as T;
    }

    return {
      data,
      status: response.status,
      headers: response.headers,
    };
  }

  function shouldRetry(status: number, attempt: number): boolean {
    return status >= 500 && attempt < maxRetries;
  }

  function getRetryDelay(attempt: number): number {
    return baseRetryDelay * Math.pow(2, attempt);
  }

  async function delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function fetchWithRetry(
    url: string,
    init: RequestInit,
    attempt = 0,
  ): Promise<Response> {
    try {
      const response = await fetch(url, init);

      if (!response.ok && shouldRetry(response.status, attempt)) {
        const retryDelayMs = getRetryDelay(attempt);
        await delay(retryDelayMs);
        return fetchWithRetry(url, init, attempt + 1);
      }

      return response;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw error;
      }
      throw new NetworkError(
        error instanceof Error ? error.message : "Network request failed",
        error instanceof Error ? error : undefined,
      );
    }
  }

  async function request<T>(
    method: string,
    path: string,
    options: GetRequestOptions & MutationRequestOptions = {},
  ): Promise<ApiResponse<T>> {
    const url = buildUrl(path, options.params);
    const headers = buildHeaders();

    const init: RequestInit = {
      method,
      headers,
      signal: options.signal,
    };

    if (options.body !== undefined) {
      init.body = JSON.stringify(options.body);
    }

    const response = await fetchWithRetry(url, init);
    return handleResponse<T>(response);
  }

  return {
    baseUrl,
    token,

    get<T>(path: string, options?: GetRequestOptions): Promise<ApiResponse<T>> {
      return request<T>("GET", path, options);
    },

    post<T>(
      path: string,
      options?: MutationRequestOptions,
    ): Promise<ApiResponse<T>> {
      return request<T>("POST", path, options);
    },

    patch<T>(
      path: string,
      options?: MutationRequestOptions,
    ): Promise<ApiResponse<T>> {
      return request<T>("PATCH", path, options);
    },

    delete<T>(
      path: string,
      options?: MutationRequestOptions,
    ): Promise<ApiResponse<T>> {
      return request<T>("DELETE", path, options);
    },
  };
}

/**
 * Query state for useApiQuery hook.
 */
export interface QueryState<T> {
  data: T | undefined;
  error: Error | undefined;
  isLoading: boolean;
  isError: boolean;
  isStale: boolean;
  refetch: () => Promise<void>;
}

/**
 * React hook for API queries with loading/error/stale handling.
 *
 * Note: This is a minimal implementation. For production use,
 * consider using a full-featured library like TanStack Query.
 *
 * @param fetcher - Function that performs the API request
 * @returns Query state with data, loading, error, and refetch
 */
export function useApiQuery<T>(_fetcher: () => Promise<T>): QueryState<T> {
  // Minimal placeholder implementation
  // In a real implementation, this would use React hooks
  return {
    data: undefined,
    error: undefined,
    isLoading: true,
    isError: false,
    isStale: false,
    refetch: async () => {
      // No-op placeholder
    },
  };
}

/** Default API client instance for convenience. */
export const apiClient = createApiClient();
