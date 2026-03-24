import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts';

interface MetricPoint {
  collected_at: string | null;
  cpu_percent: number | null;
  memory_percent: number | null;
  disk_percent_total: number | null;
  load_avg_1m: number | null;
}

interface MetricLineChartProps {
  data: MetricPoint[];
  metrics?: string[];
  height?: number;
}

const METRIC_CONFIG: Record<string, { color: string; label: string }> = {
  cpu_percent: { color: '#6366f1', label: 'CPU %' },
  memory_percent: { color: '#f59e0b', label: 'Memory %' },
  disk_percent_total: { color: '#10b981', label: 'Disk %' },
  load_avg_1m: { color: '#ef4444', label: 'Load 1m' },
};

function formatTime(ts: string | null): string {
  if (!ts) return '';
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MetricLineChart({
  data,
  metrics = ['cpu_percent', 'memory_percent', 'disk_percent_total'],
  height = 300,
}: MetricLineChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center text-gray-400 dark:text-gray-500 text-sm" style={{ height }}>
        No history data available
      </div>
    );
  }

  // Reverse so oldest is left, newest is right
  const chartData = [...data].reverse().map((d) => ({
    time: formatTime(d.collected_at),
    ...d,
  }));

  const isLoadOnly = metrics.length === 1 && metrics[0] === 'load_avg_1m';

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 11 }}
          className="fill-gray-500 dark:fill-gray-400"
          interval="preserveStartEnd"
        />
        <YAxis
          domain={isLoadOnly ? ['auto', 'auto'] : [0, 100]}
          tick={{ fontSize: 11 }}
          className="fill-gray-500 dark:fill-gray-400"
          width={40}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--tooltip-bg, #fff)',
            border: '1px solid var(--tooltip-border, #e5e7eb)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
        />
        <Legend wrapperStyle={{ fontSize: '12px' }} />
        {metrics.map((key) => {
          const config = METRIC_CONFIG[key];
          if (!config) return null;
          return (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              name={config.label}
              stroke={config.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls
            />
          );
        })}
      </LineChart>
    </ResponsiveContainer>
  );
}
