import { useAlerts } from '../hooks/useAlerts';
import StatusBadge from '../components/status/StatusBadge';
import SeverityBadge from '../components/status/SeverityBadge';
import { useSearchParams } from 'react-router-dom';

function formatTime(ts: string | null | undefined): string {
  if (!ts) return '-';
  return new Date(ts).toLocaleString();
}

export default function Alerts() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get('status') || undefined;
  const { data: alerts, isLoading, error } = useAlerts(statusFilter);

  const setFilter = (val: string | undefined) => {
    if (val) {
      setSearchParams({ status: val });
    } else {
      setSearchParams({});
    }
  };

  if (isLoading) return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading alerts...</div>;
  if (error) return <div className="text-center py-12 text-red-500 dark:text-red-400">Failed to load alerts.</div>;

  const alertList = alerts || [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Alerts</h1>
        <div className="flex space-x-2">
          {[undefined, 'OPEN', 'RESOLVED'].map((val) => (
            <button
              key={val ?? 'all'}
              onClick={() => setFilter(val)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                statusFilter === val
                  ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300'
                  : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'
              }`}
            >
              {val ?? 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Host</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Metric</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Mount</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Severity</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Message</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Triggered</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Resolved</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {alertList.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">{a.hostname ?? '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{a.metric_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 font-mono">{a.mount_path ?? '-'}</td>
                  <td className="px-4 py-3"><SeverityBadge severity={a.severity} /></td>
                  <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 max-w-xs truncate">{a.message ?? '-'}</td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{formatTime(a.triggered_at)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{formatTime(a.resolved_at)}</td>
                </tr>
              ))}
              {alertList.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">No alerts found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
