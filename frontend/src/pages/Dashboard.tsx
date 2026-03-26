import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import SummaryCard from '../components/cards/SummaryCard';
import SeverityBadge from '../components/status/SeverityBadge';
import StatusBadge from '../components/status/StatusBadge';
import MetricBar from '../components/charts/MetricBar';
import { SkeletonCard } from '../components/utils/Skeleton';
import { TimeAgo } from '../components/utils/TimeAgo';
import HostHeatmap from '../components/charts/HostHeatmap';
import { useDashboard } from '../hooks/useDashboard';
import { useAlerts } from '../hooks/useAlerts';
import { useHosts } from '../hooks/useHosts';
import { useDbMonitorSummary, useDbInstances, useDbDashboardDetails } from '../hooks/useDbMonitor';

const tabs = [
  { key: 'server', label: 'Server Monitor', icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2' },
  { key: 'db', label: 'DB Monitor', icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4' },
] as const;

type TabKey = typeof tabs[number]['key'];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabKey>('server');
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useDashboard();
  const { data: alerts } = useAlerts('OPEN');
  const { data: hosts } = useHosts();

  if (summaryLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Dashboard</h1>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
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

          {/* Host Heatmap */}
          {hosts && hosts.length > 0 && (
            <div className="mb-8">
              <HostHeatmap hosts={hosts} />
            </div>
          )}

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
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{a.hostname}</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">{a.metric_name}</span>
                        {a.triggered_at && <TimeAgo timestamp={a.triggered_at} className="text-xs text-gray-400 dark:text-gray-500" />}
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
      {activeTab === 'db' && <DbMonitorTab />}
    </div>
  );
}

function DbMonitorTab() {
  const { data: dbSummary, isLoading: summaryLoading } = useDbMonitorSummary();
  const { data: instances, isLoading: instancesLoading } = useDbInstances();
  const { data: details } = useDbDashboardDetails();
  const [slowQueryFilter, setSlowQueryFilter] = useState<number | 'all'>('all');

  const allSlowQueries = details?.top_slow_queries ?? [];
  const slowQueries = useMemo(() => {
    if (slowQueryFilter === 'all') return allSlowQueries;
    return allSlowQueries.filter(q => q.db_instance_id === slowQueryFilter);
  }, [allSlowQueries, slowQueryFilter]);

  if (summaryLoading || instancesLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    );
  }

  const tsWarnings = details?.tablespace_warnings ?? [];
  const blockingSessions = details?.blocking_sessions ?? [];

  return (
    <>
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <SummaryCard title="Total Instances" value={dbSummary?.total_instances ?? 0} color="blue" to="/db-instances" />
        <SummaryCard title="Up" value={dbSummary?.up_instances ?? 0} color="green" to="/db-instances?status=up" />
        <SummaryCard title="Down" value={dbSummary?.down_instances ?? 0} color="red" to="/db-instances?status=down" />
        <SummaryCard title="Degraded" value={dbSummary?.degraded_instances ?? 0} color="yellow" to="/db-instances?status=degraded" />
        <SummaryCard title="Active Sessions" value={dbSummary?.total_active_sessions ?? 0} color="blue" />
        <SummaryCard title="TS Warnings" value={dbSummary?.total_tablespace_warnings ?? 0} color="orange" />
      </div>

      {/* Tablespace Warnings & Blocking Sessions side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Tablespace Warnings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
            <svg className="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Tablespace Warnings</h2>
            <span className="ml-auto text-xs text-gray-400 dark:text-gray-500">&gt; 85% used</span>
          </div>
          <div className="p-4">
            {tsWarnings.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">No tablespace warnings. All within safe limits.</p>
            ) : (
              <div className="space-y-3">
                {tsWarnings.map((ts, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Link to={`/db-instances/${ts.db_instance_id}`} className="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:underline truncate">{ts.instance_name}</Link>
                        <span className="text-xs text-gray-500 dark:text-gray-400">{ts.tablespace_name}</span>
                        {ts.autoextensible === 'NO' && <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 font-medium">No AutoExt</span>}
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${ts.used_percent >= 95 ? 'bg-red-500' : 'bg-orange-500'}`}
                          style={{ width: `${Math.min(ts.used_percent, 100)}%` }}
                        />
                      </div>
                    </div>
                    <span className={`text-sm font-bold whitespace-nowrap ${ts.used_percent >= 95 ? 'text-red-600 dark:text-red-400' : 'text-orange-600 dark:text-orange-400'}`}>
                      {ts.used_percent.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Blocking Sessions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
            <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Blocking Sessions</h2>
            <span className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full ${blockingSessions.length > 0 ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'}`}>
              {blockingSessions.length}
            </span>
          </div>
          <div className="p-4">
            {blockingSessions.length === 0 ? (
              <p className="text-sm text-green-600 dark:text-green-400 text-center py-4">No blocking sessions detected.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-xs text-gray-500 dark:text-gray-400 uppercase">
                      <th className="text-left pb-2">Instance</th>
                      <th className="text-left pb-2">SID</th>
                      <th className="text-left pb-2">User</th>
                      <th className="text-left pb-2">Blocked By</th>
                      <th className="text-left pb-2">Wait Event</th>
                      <th className="text-right pb-2">Wait (s)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {blockingSessions.map((s, i) => (
                      <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td className="py-1.5 pr-2">
                          <Link to={`/db-instances/${s.db_instance_id}`} className="text-indigo-600 dark:text-indigo-400 hover:underline">{s.instance_name}</Link>
                        </td>
                        <td className="py-1.5 pr-2 font-mono text-gray-700 dark:text-gray-300">{s.sid ?? '-'}</td>
                        <td className="py-1.5 pr-2 text-gray-600 dark:text-gray-400">{s.username ?? '-'}</td>
                        <td className="py-1.5 pr-2 font-mono font-bold text-red-600 dark:text-red-400">{s.blocking_session ?? '-'}</td>
                        <td className="py-1.5 pr-2 text-gray-600 dark:text-gray-400 truncate max-w-[150px]" title={s.wait_event ?? ''}>{s.wait_event ?? '-'}</td>
                        <td className="py-1.5 text-right font-medium text-gray-700 dark:text-gray-300">{s.seconds_in_wait?.toFixed(0) ?? '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Top Slow Queries */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm mb-6">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
          <svg className="w-5 h-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Top Slow Queries</h2>
          <select
            value={slowQueryFilter}
            onChange={e => setSlowQueryFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            className="ml-auto text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 px-2 py-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="all">All Instances</option>
            {(instances ?? []).map(inst => (
              <option key={inst.id} value={inst.id}>{inst.instance_name}</option>
            ))}
          </select>
        </div>
        <div className="p-4">
          {slowQueries.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">No slow queries recorded.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 dark:text-gray-400 uppercase">
                    <th className="text-left pb-2">Instance</th>
                    <th className="text-left pb-2">SQL ID</th>
                    <th className="text-left pb-2">SQL Text</th>
                    <th className="text-left pb-2">User</th>
                    <th className="text-right pb-2">Elapsed (s)</th>
                    <th className="text-right pb-2">CPU (s)</th>
                    <th className="text-right pb-2">Buffer Gets</th>
                    <th className="text-right pb-2">Exec</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {slowQueries.map((q, i) => (
                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="py-1.5 pr-2">
                        <Link to={`/db-instances/${q.db_instance_id}`} className="text-indigo-600 dark:text-indigo-400 hover:underline">{q.instance_name}</Link>
                      </td>
                      <td className="py-1.5 pr-2 font-mono text-gray-700 dark:text-gray-300">{q.sql_id ?? '-'}</td>
                      <td className="py-1.5 pr-2 text-gray-600 dark:text-gray-400 truncate max-w-[250px]" title={q.sql_text ?? ''}>
                        {q.sql_text ? (q.sql_text.length > 60 ? q.sql_text.slice(0, 60) + '\u2026' : q.sql_text) : '-'}
                      </td>
                      <td className="py-1.5 pr-2 text-gray-600 dark:text-gray-400">{q.username ?? '-'}</td>
                      <td className="py-1.5 text-right font-bold text-gray-900 dark:text-gray-100">{q.elapsed_seconds?.toFixed(2) ?? '-'}</td>
                      <td className="py-1.5 text-right text-gray-600 dark:text-gray-400">{q.cpu_seconds?.toFixed(2) ?? '-'}</td>
                      <td className="py-1.5 text-right text-gray-600 dark:text-gray-400">{q.buffer_gets?.toLocaleString() ?? '-'}</td>
                      <td className="py-1.5 text-right text-gray-600 dark:text-gray-400">{q.executions?.toLocaleString() ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
