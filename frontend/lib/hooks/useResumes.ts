import useSWR from 'swr';
import { resumesAPI } from '@/lib/api/resumes';
import { ResumeResponse } from '@/types/api';

export function useResumes() {
  const { data, error, mutate } = useSWR<ResumeResponse[]>(
    'resumes',
    () => resumesAPI.list().then(res => res.data),
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000,
    }
  );

  return {
    resumes: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

export function useResume(id: number | null) {
  const { data, error } = useSWR<ResumeResponse>(
    id ? ['resume', id] : null,
    () => resumesAPI.get(id!).then(res => res.data)
  );

  return {
    resume: data,
    isLoading: !error && !data,
    isError: error,
  };
}
