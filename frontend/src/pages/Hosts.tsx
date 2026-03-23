import { Link, useSearchParams } from 'react-router-dom';
import { useHosts } from '../hooks/useHosts';
import StatusBadge from '../components/status/StatusBadge';
import MetricBar from '../components/charts/MetricBar';

function formatTime(ts: string | null): string {
  if (!ts) return '-';
  return new Date(ts).toLocaleString();
}

const STATUS_OPTIONS = ['all', 'healthy', 'warning', 'critical', 'stale'] as const;

export default function Hosts() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get('status') || 'all';
  const { data: hosts, isLoading, error } = useHosts();

  if (isLoading) return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading hosts...</div>;
  if (error) return <div className="text-center py-12 text-red-500 dark:text-red-400">Failed to load hosts.</div>;

  const allHosts = hosts || [];
  const hostList = statusFilter === 'all' ? allHosts : allHosts.filter((h) => h.status === statusFilter);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Hosts {statusFilter !== 'all' && <span className="text-base font-normal text-gray-500 dark:text-gray-400 capitalize">— {statusFilter}</span>}
      </h1>

      {/* Status Filter */}
      <div className="flex gap-2 mb-4">
        {STATUS_OPTIONS.map((s) => (
          <button
            key={s}
            onClick={() => s === 'all' ? setSearchParams({}) : setSearchParams({ status: s })}
            className={`px-3 py-1.5 text-sm rounded-md capitalize transition-colors ${
              statusFilter === s
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {s} {s !== 'all' ? `(${allHosts.filter((h) => h.status === s).length})` : `(${allHosts.length})`}
          </button>
        ))}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Hostname</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Environment</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">IP Address</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">CPU</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Memory</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Disk</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Last Heartbeat</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Details</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {hostList.map((h) => (
                <tr key={h.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">{h.hostname}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{h.environment ?? '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{h.ip_address ?? '-'}</td>
                  <td className="px-4 py-3"><MetricBar value={h.cpu_percent} /></td>
                  <td className="px-4 py-3"><MetricBar value={h.memory_percent} /></td>
                  <td className="px-4 py-3"><MetricBar value={h.disk_percent_total} /></td>
                  <td className="px-4 py-3"><StatusBadge status={h.status} /></td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{formatTime(h.last_heartbeat_at)}</td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/hosts/${h.id}`}
                      className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 text-sm font-medium"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
              {hostList.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">No hosts registered yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
