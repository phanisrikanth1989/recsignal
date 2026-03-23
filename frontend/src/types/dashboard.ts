export interface DashboardSummary {
  total_hosts: number;
  healthy_hosts: number;
  warning_hosts: number;
  critical_hosts: number;
  stale_hosts: number;
  active_alerts: number;
}
