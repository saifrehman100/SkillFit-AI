import apiClient from './client';
import { ResumeResponse } from '@/types/api';

export interface RewriteResponse {
  resume_id: number;
  job_id: number;
  match_id: number | null;
  original_score: number;
  improved_resume: string;
  changes_summary: string[];
  estimated_new_score: number;
  score_improvement: number;
  key_improvements: string[];
}

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

  rewrite: (resumeId: number, jobId: number, matchId?: number) =>
    apiClient.post<RewriteResponse>(`/resumes/${resumeId}/rewrite`, null, {
      params: { job_id: jobId, match_id: matchId }
    }),
};
