import { useQuery } from '@tanstack/react-query';
import { fetchHosts } from '../api/hosts';

export function useHosts() {
  return useQuery({
    queryKey: ['hosts'],
    queryFn: fetchHosts,
  });
}
