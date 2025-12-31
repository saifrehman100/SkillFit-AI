// ============ Auth ============
export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RegisterResponse {
  id: number;
  email: string;
  api_key: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
  api_key: string | null;
}

// ============ Resume ============
export interface ResumeResponse {
  id: number;
  filename: string;
  file_type: string;
  raw_text: string;
  parsed_data: Record<string, any> | null;
  created_at: string;
}

export interface ResumeListResponse {
  resumes: ResumeResponse[];
  total: number;
  page: number;
  per_page: number;
}

// ============ Job ============
export interface JobCreateRequest {
  title: string;
  company?: string;
  description: string;
  requirements?: string;
  source_url?: string;
}

export interface JobResponse {
  id: number;
  title: string;
  company: string | null;
  description: string;
  requirements: string | null;
  parsed_data: Record<string, any> | null;
  source_url: string | null;
  is_active: boolean;
  created_at: string;
}

// ============ Match ============
export interface MatchRequest {
  resume_id: number;
  job_id: number;
  detailed?: boolean;
  llm_provider?: 'openai' | 'claude' | 'gemini' | 'openai_compatible';
  llm_model?: string;
}

export interface MatchResponse {
  id: number;
  resume_id: number;
  job_id: number;
  match_score: number;
  missing_skills: string[] | null;
  recommendations: string[] | null;
  explanation: string | null;
  llm_provider: string | null;
  llm_model: string | null;
  tokens_used: number | null;
  cost_estimate: number | null;
  created_at: string;
}

// ============ Application ============
export interface ApplicationCreateRequest {
  job_id?: number;
  match_id?: number;
  company: string;
  position: string;
  status?: 'wishlist' | 'applied' | 'interview' | 'offer' | 'rejected';
  application_date?: string;
  job_url?: string;
  notes?: string;
}

export interface ApplicationUpdateRequest {
  status?: 'wishlist' | 'applied' | 'interview' | 'offer' | 'rejected';
  application_date?: string;
  job_url?: string;
  notes?: string;
}

export interface ApplicationResponse {
  id: number;
  user_id: number;
  job_id: number | null;
  match_id: number | null;
  company: string;
  position: string;
  status: 'wishlist' | 'applied' | 'interview' | 'offer' | 'rejected';
  application_date: string | null;
  job_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  job?: JobResponse;
  match?: MatchResponse;
}

// ============ LinkedIn ============
export interface LinkedInScanRequest {
  linkedin_url: string;
  resume: File;
  detailed?: boolean;
  llm_provider?: string;
  llm_model?: string;
  api_key?: string;
}

export interface LinkedInScanResponse {
  success: boolean;
  job: {
    title: string;
    company: string;
    location: string;
    source_url: string;
  };
  match: {
    score: number;
    missing_skills: string[];
    recommendations: string[];
    explanation: string;
    strengths: string[];
    weaknesses: string[];
  };
  metadata: {
    llm_provider: string;
    llm_model: string;
    tokens_used: number;
    cost_estimate: number;
  };
}

// ============ Error ============
export interface APIError {
  detail: string;
}

// ============ Stats (for dashboard) ============
export interface DashboardStats {
  total_resumes: number;
  total_jobs: number;
  total_matches: number;
  avg_match_score: number;
  total_applications: number;
}
