import apiClient from './client';
import { JobCreateRequest, JobResponse } from '@/types/api';

export const jobsAPI = {
  create: (data: JobCreateRequest, analyze = true) =>
    apiClient.post<JobResponse>(`/jobs/?analyze=${analyze}`, data),

  importFromUrl: (url: string, analyze = true) =>
    apiClient.post<JobResponse>(`/jobs/import-from-url?url=${encodeURIComponent(url)}&analyze=${analyze}`),

  list: (skip = 0, limit = 100, active_only = true) =>
    apiClient.get<JobResponse[]>('/jobs/', {
      params: { skip, limit, active_only }
    }),

  get: (id: number) =>
    apiClient.get<JobResponse>(`/jobs/${id}`),

  update: (id: number, data: JobCreateRequest) =>
    apiClient.put<JobResponse>(`/jobs/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/jobs/${id}`),
};
