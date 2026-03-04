import axios, {
  AxiosError,
  AxiosInstance,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import type { AppError, ValidationError } from '@/types/api';

const API_BASE_URL = '/api/v0';

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: unknown) => void;
    reject: (reason?: unknown) => void;
  }> = [];

  private refreshAttempts = 0;
  private readonly MAX_REFRESH_ATTEMPTS = 2;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (config.headers) {
          config.headers['X-Request-ID'] = crypto.randomUUID();
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const originalRequest =
          error.config as InternalAxiosRequestConfig;

        const isAuthRoute =
          originalRequest?.url?.includes('/auth/login') ||
          originalRequest?.url?.includes('/auth/signup') ||
          originalRequest?.url?.includes('/auth/refresh') ||
          originalRequest?.url?.includes('/auth/logout');

        const normalizedError = this.normalizeError(error);


        // Only refresh on non-auth routes to avoid infinite loops
        if (!isAuthRoute &&
          error.response?.status === 401 
        ) {
          if (this.refreshAttempts >= this.MAX_REFRESH_ATTEMPTS) {
            this.refreshAttempts = 0;
            window.location.href = '/login';
            return Promise.reject(normalizedError);
          }

          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            })
              .then(() => this.client(originalRequest))
              .catch((err) => Promise.reject(err));
          }

          this.isRefreshing = true;
          this.refreshAttempts++;

          try {
            await this.client.post('/auth/refresh');

            this.isRefreshing = false;
            this.refreshAttempts = 0;
            this.processQueue(null);

            return this.client(originalRequest);
          } catch (refreshError) {
            this.isRefreshing = false;
            this.processQueue(refreshError);

            if (this.refreshAttempts >= this.MAX_REFRESH_ATTEMPTS) {
              this.refreshAttempts = 0;
              window.location.href = '/login';
            }

            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(normalizedError);
      }
    );
  }

  private processQueue(error: unknown) {
    this.failedQueue.forEach((promise) => {
      if (error) {
        promise.reject(error);
      } else {
        promise.resolve();
      }
    });
    this.failedQueue = [];
  }

  private normalizeError(error: AxiosError): AppError {
    if (error.response?.data) {
      const data = error.response.data as AppError | ValidationError;

      if ('detail' in data) {
        return {
          code: 'validation_error',
          status_code: 422,
          message: data.detail[0]?.msg || 'Validation error',
          field: data.detail[0]?.loc[1]?.toString(),
        };
      }

      return data as AppError;
    }

    return {
      code: 'network_error',
      status_code: error.response?.status || 500,
      message: error.message || 'An unexpected error occurred',
    };
  }

  // custome helper for SSE endpoints, as axios doesn't support streaming ReadableStream
  async refreshToken(): Promise<void> {
    await this.client.post('/auth/refresh');
  }

  async get<T>(url: string, config = {}): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: unknown, config = {}): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: unknown, config = {}): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config = {}): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  async upload(url: string, file: File, config = {}): Promise<void> {
    const formData = new FormData();
    formData.append('file', file);

    await this.client.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  getClient(): AxiosInstance {
    return this.client;
  }
}

export const apiClient = new ApiClient();
export default apiClient;