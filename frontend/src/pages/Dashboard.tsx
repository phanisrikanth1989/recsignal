import { useState } from 'react';
import SummaryCard from '../components/cards/SummaryCard';
import SeverityBadge from '../components/status/SeverityBadge';
import { useDashboard } from '../hooks/useDashboard';
import { useAlerts } from '../hooks/useAlerts';

const tabs = [
  { key: 'server', label: 'Server Monitor', icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2' },
  { key: 'db', label: 'DB Monitor', icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4' },
] as const;

type TabKey = typeof tabs[number]['key'];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabKey>('server');
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

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`inline-flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors -mb-px ${
              activeTab === tab.key
                ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d={tab.icon} />
            </svg>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Server Monitor Tab */}
      {activeTab === 'server' && (
        <>
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
        </>
      )}

      {/* DB Monitor Tab */}
      {activeTab === 'db' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-12 text-center">
          <svg className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200 mb-2">DB Monitor</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm max-w-md mx-auto">
            Database monitoring is coming soon. This section will provide real-time insights into Oracle, PostgreSQL, and other database instances — including tablespace usage, active sessions, slow queries, and connection pool health.
          </p>
        </div>
      )}
    </div>
  );
}
