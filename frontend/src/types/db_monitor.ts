export interface DbInstanceListItem {
  id: number;
  instance_name: string;
  db_type: string;
  host: string | null;
  port: number | null;
  service_name: string | null;
  environment: string | null;
  status: string;
  is_active: number;
  last_seen_at: string | null;
}

export interface TablespaceItem {
  id: number;
  tablespace_name: string;
  total_mb: number | null;
  used_mb: number | null;
  free_mb: number | null;
  used_percent: number | null;
  autoextensible: string | null;
  max_mb: number | null;
  status: string | null;
  collected_at: string | null;
}

export interface DbPerformanceItem {
  buffer_cache_hit_ratio: number | null;
  library_cache_hit_ratio: number | null;
  parse_count_total: number | null;
  hard_parse_count: number | null;
  execute_count: number | null;
  user_commits: number | null;
  user_rollbacks: number | null;
  physical_reads: number | null;
  physical_writes: number | null;
  redo_size: number | null;
  sga_total_mb: number | null;
  pga_total_mb: number | null;
  active_sessions: number | null;
  inactive_sessions: number | null;
  total_sessions: number | null;
  max_sessions: number | null;
  db_uptime_seconds: number | null;
  collected_at: string | null;
}

export interface DbSessionItem {
  id: number;
  sid: number | null;
  serial_no: number | null;
  username: string | null;
  program: string | null;
  machine: string | null;
  status: string | null;
  sql_id: string | null;
  sql_text: string | null;
  wait_class: string | null;
  wait_event: string | null;
  seconds_in_wait: number | null;
  blocking_session: number | null;
  logon_time: string | null;
  elapsed_seconds: number | null;
  collected_at: string | null;
}

export interface DbSessionsSummary {
  active: number;
  inactive: number;
  total: number;
  blocking_count: number;
  long_running_count: number;
}

export interface SlowQueryItem {
  id: number;
  sql_id: string | null;
  sql_text: string | null;
  username: string | null;
  elapsed_seconds: number | null;
  cpu_seconds: number | null;
  buffer_gets: number | null;
  disk_reads: number | null;
  rows_processed: number | null;
  executions: number | null;
  plan_hash_value: string | null;
  collected_at: string | null;
}

export interface DbInstanceDetail extends DbInstanceListItem {
  support_group: string | null;
  created_at: string | null;
  tablespaces: TablespaceItem[];
  performance: DbPerformanceItem | null;
  sessions_summary: DbSessionsSummary | null;
  slow_queries: SlowQueryItem[];
}

export interface DbMonitorSummary {
  total_instances: number;
  up_instances: number;
  down_instances: number;
  degraded_instances: number;
  total_active_sessions: number;
  total_tablespace_warnings: number;
}

export interface TablespaceWarningItem {
  db_instance_id: number;
  instance_name: string;
  tablespace_name: string;
  used_percent: number;
  used_mb: number | null;
  total_mb: number | null;
  autoextensible: string | null;
}

export interface CrossInstanceSlowQuery {
  db_instance_id: number;
  instance_name: string;
  sql_id: string | null;
  sql_text: string | null;
  username: string | null;
  elapsed_seconds: number | null;
  cpu_seconds: number | null;
  buffer_gets: number | null;
  executions: number | null;
}

export interface BlockingSessionItem {
  db_instance_id: number;
  instance_name: string;
  sid: number | null;
  serial_no: number | null;
  username: string | null;
  program: string | null;
  status: string | null;
  blocking_session: number | null;
  wait_event: string | null;
  seconds_in_wait: number | null;
  sql_text: string | null;
}

export interface DbDashboardDetails {
  tablespace_warnings: TablespaceWarningItem[];
  top_slow_queries: CrossInstanceSlowQuery[];
  blocking_sessions: BlockingSessionItem[];
}
