import apiClient from './client';
import { ApplicationCreateRequest, ApplicationUpdateRequest, ApplicationResponse } from '@/types/api';

export const applicationsAPI = {
  create: (data: ApplicationCreateRequest) =>
    apiClient.post<ApplicationResponse>('/applications/', data),

  list: (status_filter?: string, skip = 0, limit = 100) =>
    apiClient.get<ApplicationResponse[]>('/applications/', {
      params: { status_filter, skip, limit }
    }),

  get: (id: number) =>
    apiClient.get<ApplicationResponse>(`/applications/${id}`),

  update: (id: number, data: ApplicationUpdateRequest) =>
    apiClient.put<ApplicationResponse>(`/applications/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/applications/${id}`),
};
