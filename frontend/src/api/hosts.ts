import apiClient from './client';
import type { HostListItem, HostDetail, ProcessItem } from '../types/host';

export async function fetchHosts(): Promise<HostListItem[]> {
  const { data } = await apiClient.get<HostListItem[]>('/api/hosts');
  return data;
}

export async function fetchHostDetail(hostId: number): Promise<HostDetail> {
  const { data } = await apiClient.get<HostDetail>(`/api/hosts/${hostId}`);
  return data;
}

export async function fetchProcesses(hostId: number, statusFilter?: string): Promise<ProcessItem[]> {
  const params = statusFilter ? { status_filter: statusFilter } : {};
  const { data } = await apiClient.get<ProcessItem[]>(`/api/hosts/${hostId}/processes`, { params });
  return data;
}
