import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  QueryRequestDto,
  QueryResponseDto,
  CourseDto,
  AssignmentDto,
  ApiResponse,
} from '@edupilot/types';

export interface ClientConfig {
  baseURL: string;
  onTokenRefresh?: (accessToken: string, refreshToken: string) => void;
  onUnauthorized?: () => void;
}

export class EduPilotClient {
  private axios: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private config: ClientConfig;

  constructor(config: ClientConfig) {
    this.config = config;
    this.axios = axios.create({
      baseURL: config.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.axios.interceptors.request.use((config) => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    // Response interceptor for error handling and token refresh
    this.axios.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            if (this.refreshToken) {
              const response = await this.refreshAccessToken(this.refreshToken);
              this.setTokens(response.accessToken, response.refreshToken);
              
              originalRequest.headers.Authorization = `Bearer ${response.accessToken}`;
              return this.axios(originalRequest);
            }
          } catch (refreshError) {
            this.config.onUnauthorized?.();
            throw refreshError;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.config.onTokenRefresh?.(accessToken, refreshToken);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.axios.post<ApiResponse<LoginResponse>>(
      '/api/v1/auth/login',
      credentials
    );
    
    const data = response.data.data!;
    this.setTokens(data.accessToken, data.refreshToken);
    return data;
  }

  async refreshAccessToken(refreshToken: string): Promise<LoginResponse> {
    const response = await this.axios.post<ApiResponse<LoginResponse>>(
      '/api/v1/auth/refresh',
      { refreshToken } as RefreshTokenRequest
    );
    return response.data.data!;
  }

  async logout() {
    this.clearTokens();
  }

  // Courses
  async getCourses(): Promise<CourseDto[]> {
    const response = await this.axios.get<ApiResponse<CourseDto[]>>(
      '/api/v1/students/courses'
    );
    return response.data.data!;
  }

  // Assignments
  async getAssignments(params?: {
    status?: string;
    upcomingOnly?: boolean;
    daysAhead?: number;
  }): Promise<AssignmentDto[]> {
    const response = await this.axios.get<ApiResponse<AssignmentDto[]>>(
      '/api/v1/students/assignments',
      { params }
    );
    return response.data.data!;
  }

  // Sync
  async syncData(): Promise<void> {
    await this.axios.post('/api/v1/students/sync');
  }

  // Query
  async submitQuery(query: QueryRequestDto): Promise<QueryResponseDto> {
    const response = await this.axios.post<ApiResponse<QueryResponseDto>>(
      '/api/v1/query',
      query
    );
    return response.data.data!;
  }

  async submitVoiceQuery(audioFile: File): Promise<QueryResponseDto> {
    const formData = new FormData();
    formData.append('audioFile', audioFile);

    const response = await this.axios.post<ApiResponse<QueryResponseDto>>(
      '/api/v1/query/voice',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data!;
  }
}
