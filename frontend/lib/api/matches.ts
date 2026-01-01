import apiClient from './client';
import { MatchRequest, MatchResponse } from '@/types/api';

export interface InterviewPrepResponse {
  technical_questions: Array<{ question: string; suggested_answer: string }>;
  behavioral_questions: Array<{ question: string; star_example: string }>;
  gap_questions: Array<{ question: string; positive_response: string }>;
  talking_points: string[];
}

export interface CoverLetterRequest {
  tone?: 'professional' | 'enthusiastic' | 'formal';
}

export interface CoverLetterResponse {
  cover_letter: string;
  candidate_name: string;
  company: string;
  job_title: string;
}

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

  // Phase 2: Interview Prep
  generateInterviewPrep: (id: number) =>
    apiClient.post<InterviewPrepResponse>(`/matches/${id}/interview-prep`),

  downloadInterviewDocx: (id: number) =>
    apiClient.get(`/matches/${id}/interview-prep/docx`, { responseType: 'blob' }),

  downloadInterviewPdf: (id: number) =>
    apiClient.get(`/matches/${id}/interview-prep/pdf`, { responseType: 'blob' }),

  // Phase 2: Cover Letter
  generateCoverLetter: (id: number, data: CoverLetterRequest = {}) =>
    apiClient.post<CoverLetterResponse>(`/matches/${id}/cover-letter`, data),

  downloadCoverLetterDocx: (id: number, tone: string = 'professional') =>
    apiClient.get(`/matches/${id}/cover-letter/docx`, {
      params: { tone },
      responseType: 'blob'
    }),
};
