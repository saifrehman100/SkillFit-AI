import useSWR from 'swr';
import { applicationsAPI } from '@/lib/api/applications';
import { ApplicationResponse } from '@/types/api';

export function useApplications(status?: string) {
  const { data, error, mutate } = useSWR<ApplicationResponse[]>(
    status ? ['applications', status] : 'applications',
    () => applicationsAPI.list(status).then(res => res.data),
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000,
    }
  );

  return {
    applications: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

export function useApplication(id: number | null) {
  const { data, error } = useSWR<ApplicationResponse>(
    id ? ['application', id] : null,
    () => applicationsAPI.get(id!).then(res => res.data)
  );

  return {
    application: data,
    isLoading: !error && !data,
    isError: error,
  };
}
