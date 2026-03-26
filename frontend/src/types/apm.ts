/* ── Business Transactions ──────────────────────────────── */

export interface BusinessTransactionItem {
  id: number;
  host_id: number | null;
  app_name: string;
  endpoint: string;
  method: string;
  status_code: number;
  response_time_ms: number;
  is_error: number;
  error_message: string | null;
  trace_id: string | null;
  collected_at: string;
}

export interface BtSummary {
  app_name: string;
  total_requests: number;
  avg_response_time_ms: number;
  error_count: number;
  error_rate: number;
  p95_response_time_ms: number | null;
}

/* ── Distributed Tracing ───────────────────────────────── */

export interface TraceListItem {
  id: number;
  trace_id: string;
  root_service: string;
  root_endpoint: string | null;
  root_method: string | null;
  status_code: number | null;
  total_duration_ms: number;
  span_count: number;
  has_error: number;
  started_at: string;
}

export interface SpanItem {
  id: number;
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  service_name: string;
  operation_name: string;
  span_kind: string;
  status: string;
  duration_ms: number;
  started_at: string;
  attributes: string | null;
  events: string | null;
}

export interface TraceDetail extends TraceListItem {
  spans: SpanItem[];
}

/* ── Baselines & Anomalies ─────────────────────────────── */

export interface BaselineItem {
  id: number;
  host_id: number;
  metric_name: string;
  mean: number;
  stddev: number;
  min_val: number;
  max_val: number;
  sample_count: number;
  window_hours: number;
  computed_at: string;
}

export interface AnomalyItem {
  id: number;
  host_id: number;
  hostname: string | null;
  metric_name: string;
  observed_value: number;
  baseline_mean: number;
  baseline_stddev: number;
  deviation_sigma: number;
  severity: string;
  status: string;
  detected_at: string;
  resolved_at: string | null;
}

export interface AnomalySummary {
  total_anomalies: number;
  open_anomalies: number;
  warning_count: number;
  critical_count: number;
}

/* ── Log Analytics ─────────────────────────────────────── */

export interface LogItem {
  id: number;
  host_id: number;
  hostname: string;
  source: string;
  level: string;
  message: string;
  trace_id: string | null;
  logged_at: string;
}

export interface LogSearchResult {
  total: number;
  logs: LogItem[];
}

export interface LogSummary {
  total_logs: number;
  error_count: number;
  warn_count: number;
  info_count: number;
}

/* ── Service Topology ──────────────────────────────────── */

export interface ServiceNodeItem {
  id: number;
  service_name: string;
  service_type: string;
  host_id: number | null;
  status: string;
  avg_response_time_ms: number | null;
  request_rate: number | null;
  error_rate: number | null;
  last_seen_at: string | null;
}

export interface ServiceDependencyItem {
  id: number;
  source_service: string;
  target_service: string;
  call_count: number;
  error_count: number;
  avg_duration_ms: number | null;
  last_seen_at: string;
}

export interface TopologyGraph {
  nodes: ServiceNodeItem[];
  edges: ServiceDependencyItem[];
}

/* ── Code-Level Diagnostics ────────────────────────────── */

export interface DiagnosticSnapshotItem {
  id: number;
  host_id: number | null;
  app_name: string;
  snapshot_type: string;
  duration_seconds: number | null;
  top_functions: string | null;
  memory_summary: string | null;
  thread_dump: string | null;
  triggered_by: string | null;
  collected_at: string;
}
