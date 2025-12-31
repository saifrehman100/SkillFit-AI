import useSWR from 'swr';
import { matchesAPI } from '@/lib/api/matches';
import { MatchResponse } from '@/types/api';

export function useMatches() {
  const { data, error, mutate } = useSWR<MatchResponse[]>(
    'matches',
    () => matchesAPI.list().then(res => res.data),
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000,
    }
  );

  return {
    matches: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

export function useMatch(id: number | null) {
  const { data, error } = useSWR<MatchResponse>(
    id ? ['match', id] : null,
    () => matchesAPI.get(id!).then(res => res.data)
  );

  return {
    match: data,
    isLoading: !error && !data,
    isError: error,
  };
}
