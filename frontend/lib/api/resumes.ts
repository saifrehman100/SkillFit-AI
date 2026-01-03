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

  getMatchesCount: (id: number) =>
    apiClient.get<{ matches_count: number }>(`/resumes/${id}/matches-count`),

  delete: (id: number, keepMatches = false) =>
    apiClient.delete(`/resumes/${id}`, {
      params: { keep_matches: keepMatches }
    }),

  rewrite: (resumeId: number, jobId: number, matchId?: number) =>
    apiClient.post<RewriteResponse>(`/resumes/${resumeId}/rewrite`, null, {
      params: { job_id: jobId, match_id: matchId }
    }),

  // Phase 2: Resume Downloads
  downloadDocx: (id: number) =>
    apiClient.get(`/resumes/${id}/download-docx`, { responseType: 'blob' }),

  downloadPdf: (id: number) =>
    apiClient.get(`/resumes/${id}/download-pdf`, { responseType: 'blob' }),

  // Phase 2: Improved Resume Management
  downloadImprovedResume: (matchId: number, format: 'pdf' | 'docx') =>
    apiClient.get(`/resumes/improved/${matchId}/download`, {
      params: { format },
      responseType: 'blob'
    }),

  saveImprovedResume: (matchId: number) =>
    apiClient.post<{ message: string; resume: ResumeResponse; can_use_for_matching: boolean }>(
      `/resumes/improved/${matchId}/save`
    ),

  rescanImprovedResume: (matchId: number, saveToCollection: boolean = false) =>
    apiClient.post(`/resumes/improved/${matchId}/rescan`, null, {
      params: { save_to_collection: saveToCollection }
    }),
};
