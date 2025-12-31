import useSWR from 'swr';
import { jobsAPI } from '@/lib/api/jobs';
import { JobResponse } from '@/types/api';

export function useJobs(activeOnly = true) {
  const { data, error, mutate } = useSWR<JobResponse[]>(
    ['jobs', activeOnly],
    () => jobsAPI.list(0, 100, activeOnly).then(res => res.data),
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000,
    }
  );

  return {
    jobs: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

export function useJob(id: number | null) {
  const { data, error } = useSWR<JobResponse>(
    id ? ['job', id] : null,
    () => jobsAPI.get(id!).then(res => res.data)
  );

  return {
    job: data,
    isLoading: !error && !data,
    isError: error,
  };
}
