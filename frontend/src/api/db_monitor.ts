import apiClient from './client';
import type {
  DbMonitorSummary,
  DbInstanceListItem,
  DbInstanceDetail,
  DbSessionItem,
} from '../types/db_monitor';

export async function fetchDbMonitorSummary(): Promise<DbMonitorSummary> {
  const { data } = await apiClient.get<DbMonitorSummary>('/api/db-monitor/summary');
  return data;
}

export async function fetchDbInstances(): Promise<DbInstanceListItem[]> {
  const { data } = await apiClient.get<DbInstanceListItem[]>('/api/db-monitor/instances');
  return data;
}

export async function fetchDbInstanceDetail(instanceId: number): Promise<DbInstanceDetail> {
  const { data } = await apiClient.get<DbInstanceDetail>(`/api/db-monitor/instances/${instanceId}`);
  return data;
}

export async function fetchDbSessions(instanceId: number, status?: string): Promise<DbSessionItem[]> {
  const params = status ? { status } : {};
  const { data } = await apiClient.get<DbSessionItem[]>(`/api/db-monitor/instances/${instanceId}/sessions`, { params });
  return data;
}
