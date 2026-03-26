import { useQuery } from '@tanstack/react-query';
import {
  fetchTransactions, fetchBtSummary, fetchAppNames,
  fetchTraces, fetchTraceDetail, fetchServices,
  fetchTopology,
  fetchBaselines, fetchAnomalies, fetchAnomalySummary,
  searchLogs, fetchLogSummary, fetchLogSources,
  fetchDiagnostics, fetchDiagnosticDetail,
} from '../api/apm';

// ── Business Transactions ────────────────────────────────

export function useTransactions(appName?: string) {
  return useQuery({
    queryKey: ['apm-transactions', appName],
    queryFn: () => fetchTransactions(appName),
  });
}

export function useBtSummary() {
  return useQuery({
    queryKey: ['apm-bt-summary'],
    queryFn: fetchBtSummary,
  });
}

export function useAppNames() {
  return useQuery({
    queryKey: ['apm-app-names'],
    queryFn: fetchAppNames,
  });
}

// ── Distributed Tracing ──────────────────────────────────

export function useTraces(service?: string, hasError?: boolean) {
  return useQuery({
    queryKey: ['apm-traces', service, hasError],
    queryFn: () => fetchTraces(service, hasError),
  });
}

export function useTraceDetail(traceId: string) {
  return useQuery({
    queryKey: ['apm-trace', traceId],
    queryFn: () => fetchTraceDetail(traceId),
    enabled: !!traceId,
  });
}

export function useServices() {
  return useQuery({
    queryKey: ['apm-services'],
    queryFn: fetchServices,
  });
}

// ── Topology ─────────────────────────────────────────────

export function useTopology() {
  return useQuery({
    queryKey: ['apm-topology'],
    queryFn: fetchTopology,
  });
}

// ── Baselines & Anomalies ────────────────────────────────

export function useBaselines(hostId: number) {
  return useQuery({
    queryKey: ['apm-baselines', hostId],
    queryFn: () => fetchBaselines(hostId),
    enabled: !!hostId,
  });
}

export function useAnomalies(hostId?: number, status?: string) {
  return useQuery({
    queryKey: ['apm-anomalies', hostId, status],
    queryFn: () => fetchAnomalies(hostId, status),
  });
}

export function useAnomalySummary() {
  return useQuery({
    queryKey: ['apm-anomaly-summary'],
    queryFn: fetchAnomalySummary,
  });
}

// ── Log Analytics ────────────────────────────────────────

export function useLogs(query?: string, hostId?: number, level?: string, source?: string) {
  return useQuery({
    queryKey: ['apm-logs', query, hostId, level, source],
    queryFn: () => searchLogs(query, hostId, level, source),
  });
}

export function useLogSummary() {
  return useQuery({
    queryKey: ['apm-log-summary'],
    queryFn: fetchLogSummary,
  });
}

export function useLogSources() {
  return useQuery({
    queryKey: ['apm-log-sources'],
    queryFn: fetchLogSources,
  });
}

// ── Diagnostics ──────────────────────────────────────────

export function useDiagnostics(appName?: string, snapshotType?: string) {
  return useQuery({
    queryKey: ['apm-diagnostics', appName, snapshotType],
    queryFn: () => fetchDiagnostics(appName, snapshotType),
  });
}

export function useDiagnosticDetail(snapshotId: number) {
  return useQuery({
    queryKey: ['apm-diagnostic', snapshotId],
    queryFn: () => fetchDiagnosticDetail(snapshotId),
    enabled: !!snapshotId,
  });
}
