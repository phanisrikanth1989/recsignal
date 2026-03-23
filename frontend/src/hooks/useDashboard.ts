import { useQuery } from '@tanstack/react-query';
import { fetchDashboardSummary } from '../api/dashboard';

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
  });
}
