import apiClient from './client';
import { MatchRequest, MatchResponse } from '@/types/api';

export const matchesAPI = {
  create: (data: MatchRequest) =>
    apiClient.post<MatchResponse>('/matches/', data),

  list: (skip = 0, limit = 100) =>
    apiClient.get<MatchResponse[]>('/matches/', {
      params: { skip, limit }
    }),

  get: (id: number) =>
    apiClient.get<MatchResponse>(`/matches/${id}`),

  delete: (id: number) =>
    apiClient.delete(`/matches/${id}`),
};
