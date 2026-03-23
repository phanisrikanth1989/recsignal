import SummaryCard from '../components/cards/SummaryCard';
import SeverityBadge from '../components/status/SeverityBadge';
import { useDashboard } from '../hooks/useDashboard';
import { useAlerts } from '../hooks/useAlerts';

export default function Dashboard() {
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useDashboard();
  const { data: alerts } = useAlerts('OPEN');

  if (summaryLoading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading dashboard...</div>;
  }

  if (summaryError) {
    return <div className="text-center py-12 text-red-500 dark:text-red-400">Failed to load dashboard data.</div>;
  }

  const recentAlerts = (alerts || []).slice(0, 10);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Dashboard</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <SummaryCard title="Total Hosts" value={summary?.total_hosts ?? 0} color="blue" to="/hosts" />
        <SummaryCard title="Healthy" value={summary?.healthy_hosts ?? 0} color="green" to="/hosts?status=healthy" />
        <SummaryCard title="Warning" value={summary?.warning_hosts ?? 0} color="yellow" to="/hosts?status=warning" />
        <SummaryCard title="Critical" value={summary?.critical_hosts ?? 0} color="red" to="/hosts?status=critical" />
        <SummaryCard title="Stale" value={summary?.stale_hosts ?? 0} color="gray" to="/hosts?status=stale" />
        <SummaryCard title="Active Alerts" value={summary?.active_alerts ?? 0} color="orange" to="/alerts?status=OPEN" />
      </div>

      {/* Recent Alerts */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Recent Alerts</h2>
        </div>
        <div className="p-4">
          {recentAlerts.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-sm">No active alerts.</p>
          ) : (
            <div className="space-y-2">
              {recentAlerts.map((a) => (
                <div key={a.id} className="flex items-center justify-between py-1.5 border-b border-gray-100 dark:border-gray-700 last:border-0">
                  <div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{a.hostname}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">{a.metric_name}</span>
                  </div>
                  <SeverityBadge severity={a.severity} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
