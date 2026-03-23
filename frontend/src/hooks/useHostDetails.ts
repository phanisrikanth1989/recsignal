import { useQuery } from '@tanstack/react-query';
import { fetchHostDetail } from '../api/hosts';

export function useHostDetails(hostId: number) {
  return useQuery({
    queryKey: ['host-detail', hostId],
    queryFn: () => fetchHostDetail(hostId),
    enabled: !!hostId,
  });
}
