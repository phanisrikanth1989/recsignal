import { useQuery } from '@tanstack/react-query';
import {
  fetchDbMonitorSummary,
  fetchDbInstances,
  fetchDbInstanceDetail,
  fetchDbSessions,
  fetchDbDashboardDetails,
} from '../api/db_monitor';

export function useDbMonitorSummary() {
  return useQuery({
    queryKey: ['db-monitor-summary'],
    queryFn: fetchDbMonitorSummary,
  });
}

export function useDbInstances() {
  return useQuery({
    queryKey: ['db-instances'],
    queryFn: fetchDbInstances,
  });
}

export function useDbInstanceDetail(instanceId: number | null) {
  return useQuery({
    queryKey: ['db-instance-detail', instanceId],
    queryFn: () => fetchDbInstanceDetail(instanceId!),
    enabled: instanceId !== null,
  });
}

export function useDbSessions(instanceId: number | null, status?: string) {
  return useQuery({
    queryKey: ['db-sessions', instanceId, status],
    queryFn: () => fetchDbSessions(instanceId!, status),
    enabled: instanceId !== null,
  });
}

export function useDbDashboardDetails() {
  return useQuery({
    queryKey: ['db-dashboard-details'],
    queryFn: fetchDbDashboardDetails,
  });
}
