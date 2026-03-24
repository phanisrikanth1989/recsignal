import { Link } from 'react-router-dom';

interface HeatmapHost {
  id: number;
  hostname: string;
  status: string;
  cpu_percent: number | null;
}

interface HostHeatmapProps {
  hosts: HeatmapHost[];
}

const statusColor: Record<string, string> = {
  healthy: 'bg-green-500 hover:bg-green-400',
  warning: 'bg-yellow-500 hover:bg-yellow-400',
  critical: 'bg-red-500 hover:bg-red-400',
  stale: 'bg-gray-400 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500',
  unknown: 'bg-gray-300 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600',
};

export default function HostHeatmap({ hosts }: HostHeatmapProps) {
  if (!hosts || hosts.length === 0) {
    return <p className="text-sm text-gray-400 dark:text-gray-500">No hosts registered.</p>;
  }

  return (
    <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2">
      {hosts.map((h) => (
        <Link
          key={h.id}
          to={`/hosts/${h.id}`}
          title={`${h.hostname} — ${h.status}${h.cpu_percent != null ? ` — CPU: ${h.cpu_percent.toFixed(1)}%` : ''}`}
          className={`rounded-lg p-2 text-center transition-all hover:scale-105 hover:shadow-md ${statusColor[h.status] || statusColor.unknown}`}
        >
          <p className="text-[10px] font-medium text-white truncate leading-tight">
            {h.hostname}
          </p>
          {h.cpu_percent != null && (
            <p className="text-[9px] text-white/80 mt-0.5">{h.cpu_percent.toFixed(0)}%</p>
          )}
        </Link>
      ))}
    </div>
  );
}
