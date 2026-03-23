import { useQuery } from '@tanstack/react-query';
import { fetchAlerts } from '../api/alerts';

export function useAlerts(status?: string) {
  return useQuery({
    queryKey: ['alerts', status],
    queryFn: () => fetchAlerts(status),
  });
}
