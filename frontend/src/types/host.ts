export interface HostListItem {
  id: number;
  hostname: string;
  ip_address: string | null;
  environment: string | null;
  status: string;
  cpu_percent: number | null;
  memory_percent: number | null;
  disk_percent_total: number | null;
  last_heartbeat_at: string | null;
}

export interface MountUsage {
  mount_path: string;
  total_gb: number | null;
  used_gb: number | null;
  used_percent: number | null;
  collected_at: string | null;
}

export interface HostDetail {
  id: number;
  hostname: string;
  ip_address: string | null;
  environment: string | null;
  support_group: string | null;
  is_active: number;
  last_seen_at: string | null;
  created_at: string | null;
  status: string;
  cpu_percent: number | null;
  memory_percent: number | null;
  disk_percent_total: number | null;
  load_avg_1m: number | null;
  last_heartbeat_at: string | null;
  collected_at: string | null;
  mounts: MountUsage[];
  recent_history: MetricHistoryItem[];
  active_alerts: HostAlert[];
}

export interface MetricHistoryItem {
  id: number;
  cpu_percent: number | null;
  memory_percent: number | null;
  disk_percent_total: number | null;
  load_avg_1m: number | null;
  collected_at: string | null;
}

export interface HostAlert {
  id: number;
  metric_name: string;
  severity: string;
  message: string;
  triggered_at: string | null;
}
