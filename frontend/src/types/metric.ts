export interface MetricSnapshot {
  cpu_percent: number | null;
  memory_percent: number | null;
  disk_percent_total: number | null;
  load_avg_1m: number | null;
  collected_at: string | null;
}
