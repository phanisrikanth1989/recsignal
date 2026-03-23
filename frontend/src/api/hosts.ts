import apiClient from './client';
import type { HostListItem, HostDetail } from '../types/host';

export async function fetchHosts(): Promise<HostListItem[]> {
  const { data } = await apiClient.get<HostListItem[]>('/api/hosts');
  return data;
}

export async function fetchHostDetail(hostId: number): Promise<HostDetail> {
  const { data } = await apiClient.get<HostDetail>(`/api/hosts/${hostId}`);
  return data;
}
