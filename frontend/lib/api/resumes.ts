import apiClient from './client';
import { ResumeResponse } from '@/types/api';

export const resumesAPI = {
  upload: (file: File, analyze = true) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<ResumeResponse>(`/resumes/upload?analyze=${analyze}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  list: (skip = 0, limit = 100) =>
    apiClient.get<ResumeResponse[]>('/resumes/', {
      params: { skip, limit }
    }),

  get: (id: number) =>
    apiClient.get<ResumeResponse>(`/resumes/${id}`),

  delete: (id: number) =>
    apiClient.delete(`/resumes/${id}`),
};
