import apiClient from './client';
import type {
  BusinessTransactionItem, BtSummary,
  TraceListItem, TraceDetail,
  BaselineItem, AnomalyItem, AnomalySummary,
  LogSearchResult, LogSummary,
  TopologyGraph,
  DiagnosticSnapshotItem,
} from '../types/apm';

// ── Business Transactions ────────────────────────────────

export async function fetchTransactions(appName?: string, limit = 200): Promise<BusinessTransactionItem[]> {
  const params: Record<string, string | number> = { limit };
  if (appName) params.app_name = appName;
  const { data } = await apiClient.get<BusinessTransactionItem[]>('/api/apm/transactions', { params });
  return data;
}

export async function fetchBtSummary(): Promise<BtSummary[]> {
  const { data } = await apiClient.get<BtSummary[]>('/api/apm/transactions/summary');
  return data;
}

export async function fetchAppNames(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/api/apm/transactions/apps');
  return data;
}

// ── Distributed Tracing ──────────────────────────────────

export async function fetchTraces(service?: string, hasError?: boolean, limit = 100): Promise<TraceListItem[]> {
  const params: Record<string, string | number | boolean> = { limit };
  if (service) params.service = service;
  if (hasError !== undefined) params.has_error = hasError;
  const { data } = await apiClient.get<TraceListItem[]>('/api/apm/traces', { params });
  return data;
}

export async function fetchTraceDetail(traceId: string): Promise<TraceDetail> {
  const { data } = await apiClient.get<TraceDetail>(`/api/apm/traces/${traceId}`);
  return data;
}

export async function fetchServices(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/api/apm/services');
  return data;
}

// ── Topology ─────────────────────────────────────────────

export async function fetchTopology(): Promise<TopologyGraph> {
  const { data } = await apiClient.get<TopologyGraph>('/api/apm/topology');
  return data;
}

// ── Baselines & Anomalies ────────────────────────────────

export async function fetchBaselines(hostId: number): Promise<BaselineItem[]> {
  const { data } = await apiClient.get<BaselineItem[]>(`/api/apm/baselines/${hostId}`);
  return data;
}

export async function computeBaselines(hostId: number): Promise<BaselineItem[]> {
  const { data } = await apiClient.post<BaselineItem[]>(`/api/apm/baselines/compute/${hostId}`);
  return data;
}

export async function fetchAnomalies(hostId?: number, status?: string, limit = 200): Promise<AnomalyItem[]> {
  const params: Record<string, string | number> = { limit };
  if (hostId) params.host_id = hostId;
  if (status) params.status = status;
  const { data } = await apiClient.get<AnomalyItem[]>('/api/apm/anomalies', { params });
  return data;
}

export async function fetchAnomalySummary(): Promise<AnomalySummary> {
  const { data } = await apiClient.get<AnomalySummary>('/api/apm/anomalies/summary');
  return data;
}

// ── Log Analytics ────────────────────────────────────────

export async function searchLogs(
  query?: string, hostId?: number, level?: string, source?: string, limit = 200, offset = 0,
): Promise<LogSearchResult> {
  const params: Record<string, string | number> = { limit, offset };
  if (query) params.query = query;
  if (hostId) params.host_id = hostId;
  if (level) params.level = level;
  if (source) params.source = source;
  const { data } = await apiClient.get<LogSearchResult>('/api/apm/logs', { params });
  return data;
}

export async function fetchLogSummary(): Promise<LogSummary> {
  const { data } = await apiClient.get<LogSummary>('/api/apm/logs/summary');
  return data;
}

export async function fetchLogSources(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/api/apm/logs/sources');
  return data;
}

// ── Diagnostics ──────────────────────────────────────────

export async function fetchDiagnostics(appName?: string, snapshotType?: string, limit = 50): Promise<DiagnosticSnapshotItem[]> {
  const params: Record<string, string | number> = { limit };
  if (appName) params.app_name = appName;
  if (snapshotType) params.snapshot_type = snapshotType;
  const { data } = await apiClient.get<DiagnosticSnapshotItem[]>('/api/apm/diagnostics', { params });
  return data;
}

export async function fetchDiagnosticDetail(snapshotId: number): Promise<DiagnosticSnapshotItem> {
  const { data } = await apiClient.get<DiagnosticSnapshotItem>(`/api/apm/diagnostics/${snapshotId}`);
  return data;
}
