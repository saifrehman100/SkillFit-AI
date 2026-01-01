import apiClient from './client';

export interface AnalyticsEvent {
  event_type: string;
  event_data?: Record<string, any>;
}

export interface AnalyticsStats {
  total_events: number;
  events_by_type: Record<string, number>;
  daily_events: Array<{ date: string; count: number }>;
  top_pages: Array<{ page: string; views: number }>;
}

export const analyticsAPI = {
  // Track an analytics event
  track: (data: AnalyticsEvent) =>
    apiClient.post('/analytics/track', data),

  // Get user's analytics stats
  getStats: (days: number = 30) =>
    apiClient.get<AnalyticsStats>('/analytics/stats', {
      params: { days }
    }),
};
