import { useParams } from 'react-router-dom';
import { useHostDetails } from '../hooks/useHostDetails';
import StatusBadge from '../components/status/StatusBadge';
import SeverityBadge from '../components/status/SeverityBadge';
import MetricBar from '../components/charts/MetricBar';

function formatTime(ts: string | null | undefined): string {
  if (!ts) return '-';
  return new Date(ts).toLocaleString();
}

export default function HostDetails() {
  const { hostId } = useParams<{ hostId: string }>();
  const id = Number(hostId);
  const { data: host, isLoading, error } = useHostDetails(id);

  if (isLoading) return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading host details...</div>;
  if (error || !host) return <div className="text-center py-12 text-red-500 dark:text-red-400">Host not found.</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{host.hostname}</h1>
        <StatusBadge status={host.status} />
      </div>

      {/* Host Metadata */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Host Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-gray-500 dark:text-gray-400">IP Address:</span> <span className="font-medium dark:text-gray-200">{host.ip_address ?? '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Environment:</span> <span className="font-medium dark:text-gray-200">{host.environment ?? '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Support Group:</span> <span className="font-medium dark:text-gray-200">{host.support_group ?? '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Last Seen:</span> <span className="font-medium dark:text-gray-200">{formatTime(host.last_seen_at)}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Last Heartbeat:</span> <span className="font-medium dark:text-gray-200">{formatTime(host.last_heartbeat_at)}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Metrics At:</span> <span className="font-medium dark:text-gray-200">{formatTime(host.collected_at)}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Registered:</span> <span className="font-medium dark:text-gray-200">{formatTime(host.created_at)}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Active:</span> <span className="font-medium dark:text-gray-200">{host.is_active ? 'Yes' : 'No'}</span></div>
        </div>
      </div>

      {/* Latest Metrics */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Latest Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">CPU Usage</p>
            <MetricBar value={host.cpu_percent} />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Memory Usage</p>
            <MetricBar value={host.memory_percent} />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Disk Usage (Total)</p>
            <MetricBar value={host.disk_percent_total} />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Load Average (1m)</p>
            <p className="text-lg font-semibold text-gray-800 dark:text-gray-100">{host.load_avg_1m?.toFixed(2) ?? '-'}</p>
          </div>
        </div>
      </div>

      {/* Mount Usage */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Mount Usage</h2>
        {host.mounts.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">No mount data available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Mount Path</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Total (GB)</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Used (GB)</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Usage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {host.mounts.map((m, i) => (
                  <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-2 text-sm font-mono text-gray-700 dark:text-gray-300">{m.mount_path}</td>
                    <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{m.total_gb?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{m.used_gb?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-2"><MetricBar value={m.used_percent} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent History */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Recent Metric History</h2>
        {host.recent_history.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">No history available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Time</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">CPU %</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Memory %</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Disk %</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Load 1m</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {host.recent_history.slice(0, 20).map((r, i) => (
                  <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{formatTime(r.collected_at)}</td>
                    <td className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">{r.cpu_percent?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">{r.memory_percent?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">{r.disk_percent_total?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">{r.load_avg_1m?.toFixed(2) ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Active Alerts */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Active Alerts</h2>
        {host.active_alerts.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">No active alerts.</p>
        ) : (
          <div className="space-y-2">
            {host.active_alerts.map((a) => (
              <div key={a.id} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                <div>
                  <span className="text-sm text-gray-700 dark:text-gray-300">{a.message}</span>
                  <span className="text-xs text-gray-400 dark:text-gray-500 ml-2">{formatTime(a.triggered_at)}</span>
                </div>
                <SeverityBadge severity={a.severity} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
