import apiClient from './client';
import { RegisterRequest, RegisterResponse, LoginRequest, LoginResponse, UserResponse } from '@/types/api';

export const authAPI = {
  register: (data: RegisterRequest) =>
    apiClient.post<RegisterResponse>('/auth/register', data),

  login: (data: LoginRequest) =>
    apiClient.post<LoginResponse>('/auth/login', data),

  getCurrentUser: () =>
    apiClient.get<UserResponse>('/auth/me'),

  regenerateAPIKey: () =>
    apiClient.post<{ api_key: string }>('/auth/api-key/regenerate'),
};
