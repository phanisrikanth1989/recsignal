import apiClient from './client';
import type { DashboardSummary } from '../types/dashboard';

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>('/api/dashboard/summary');
  return data;
}
