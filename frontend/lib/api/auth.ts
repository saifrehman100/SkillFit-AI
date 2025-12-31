import apiClient from './client';
import { RegisterRequest, RegisterResponse, LoginRequest, LoginResponse, UserResponse } from '@/types/api';

export interface LLMSettingsUpdate {
  provider?: string;
  model?: string;
}

export interface LLMSettingsResponse {
  provider: string | null;
  model: string | null;
  available_providers: string[];
}

export interface UsageResponse {
  plan: string;
  matches_used: number;
  matches_limit: number;
  matches_remaining: number;
  can_create_match: boolean;
}

export const authAPI = {
  register: (data: RegisterRequest) =>
    apiClient.post<RegisterResponse>('/auth/register', data),

  login: (data: LoginRequest) =>
    apiClient.post<LoginResponse>('/auth/login', data),

  getCurrentUser: () =>
    apiClient.get<UserResponse>('/auth/me'),

  regenerateAPIKey: () =>
    apiClient.post<{ api_key: string }>('/auth/api-key/regenerate'),

  getLLMSettings: () =>
    apiClient.get<LLMSettingsResponse>('/auth/llm-settings'),

  updateLLMSettings: (data: LLMSettingsUpdate) =>
    apiClient.put<LLMSettingsResponse>('/auth/llm-settings', data),

  getUsage: () =>
    apiClient.get<UsageResponse>('/auth/usage'),
};
