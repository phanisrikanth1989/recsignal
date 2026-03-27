import { useAlerts } from '../hooks/useAlerts';
import StatusBadge from '../components/status/StatusBadge';
import SeverityBadge from '../components/status/SeverityBadge';
import { useSearchParams } from 'react-router-dom';
import { TimeAgo } from '../components/utils/TimeAgo';
import { SkeletonTable } from '../components/utils/Skeleton';
import type { AlertListItem } from '../types/alert';

function exportAlertCSV(alerts: AlertListItem[]) {
  const header = 'Host,Metric,Mount,Severity,Message,Status,Triggered,Resolved';
  const rows = alerts.map(a =>
    [a.hostname ?? '', a.metric_name, a.mount_path ?? '', a.severity, (a.message ?? '').replace(/,/g, ';'), a.status, a.triggered_at ?? '', a.resolved_at ?? ''].join(',')
  );
  const blob = new Blob([header + '\n' + rows.join('\n')], { type: 'text/csv' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `alerts-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

export default function Alerts() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get('status') || undefined;
  const { data: alerts, isLoading, error } = useAlerts(statusFilter);
  const alertList = alerts || [];

  const setFilter = (val: string | undefined) => {
    if (val) {
      setSearchParams({ status: val });
    } else {
      setSearchParams({});
    }
  };

  if (isLoading) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Alerts</h1>
      <SkeletonTable rows={6} cols={6} />
    </div>
  );
  if (error) return <div className="text-center py-12 text-red-500 dark:text-red-400">Failed to load alerts.</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Alerts</h1>
        <div className="flex items-center space-x-2">
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
          <button
            onClick={() => exportAlertCSV(alertList)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            title="Export to CSV"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            CSV
          </button>
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
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {a.triggered_at ? <TimeAgo timestamp={a.triggered_at} /> : '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {a.resolved_at ? <TimeAgo timestamp={a.resolved_at} /> : '-'}
                  </td>
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
