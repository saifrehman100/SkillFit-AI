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

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface GoogleAuthResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface ProInterestRequest {
  email: string;
  feature_interested_in?: string;
}

export interface ContactSalesRequest {
  email: string;
  plan: string;
  message: string;
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

  // Phase 2: Forgot Password
  forgotPassword: (data: ForgotPasswordRequest) =>
    apiClient.post<{ message: string }>('/auth/forgot-password', data),

  resetPassword: (data: ResetPasswordRequest) =>
    apiClient.post<{ message: string }>('/auth/reset-password', data),

  // Phase 2: Google OAuth
  googleAuth: (code: string) =>
    apiClient.post<GoogleAuthResponse>('/auth/google', { code }),

  // Pro Plan Interest
  expressProInterest: (data: ProInterestRequest) =>
    apiClient.post<{ message: string; status: string }>('/auth/pro-interest', data),

  // Contact Sales for Enterprise
  contactSales: (data: ContactSalesRequest) =>
    apiClient.post<{ message: string }>('/auth/contact-sales', data),

  // Get Pricing Info
  getPricing: () =>
    apiClient.get('/auth/pricing'),
};
