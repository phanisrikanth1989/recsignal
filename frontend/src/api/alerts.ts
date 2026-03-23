import apiClient from './client';
import type { AlertListItem } from '../types/alert';

export async function fetchAlerts(status?: string): Promise<AlertListItem[]> {
  const params = status ? { status } : {};
  const { data } = await apiClient.get<AlertListItem[]>('/api/alerts', { params });
  return data;
}
