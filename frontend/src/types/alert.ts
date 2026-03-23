export interface AlertListItem {
  id: number;
  host_id: number;
  hostname: string | null;
  metric_name: string;
  mount_path: string | null;
  severity: string;
  message: string | null;
  status: string;
  triggered_at: string | null;
  resolved_at: string | null;
}
