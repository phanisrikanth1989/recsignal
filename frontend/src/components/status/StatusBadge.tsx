const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
  healthy: { bg: 'bg-green-100', text: 'text-green-800', label: 'Healthy' },
  warning: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Warning' },
  critical: { bg: 'bg-red-100', text: 'text-red-800', label: 'Critical' },
  stale: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Stale' },
  unknown: { bg: 'bg-gray-100', text: 'text-gray-500', label: 'Unknown' },
  OPEN: { bg: 'bg-red-100', text: 'text-red-800', label: 'Open' },
  RESOLVED: { bg: 'bg-green-100', text: 'text-green-800', label: 'Resolved' },
  up: { bg: 'bg-green-100', text: 'text-green-800', label: 'Up' },
  down: { bg: 'bg-red-100', text: 'text-red-800', label: 'Down' },
  degraded: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Degraded' },
};

export default function StatusBadge({ status }: { status: string }) {
  const cfg = statusConfig[status] || statusConfig.unknown;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      {cfg.label}
    </span>
  );
}
