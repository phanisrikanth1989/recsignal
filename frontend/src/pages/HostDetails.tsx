import { useParams } from 'react-router-dom';
import { useState, useMemo } from 'react';
import { useHostDetails } from '../hooks/useHostDetails';
import StatusBadge from '../components/status/StatusBadge';
import SeverityBadge from '../components/status/SeverityBadge';
import MetricBar from '../components/charts/MetricBar';
import ProcessListModal from '../components/modals/ProcessListModal';
import GaugeChart from '../components/charts/GaugeChart';
import MetricLineChart from '../components/charts/MetricLineChart';
import { TimeAgo } from '../components/utils/TimeAgo';
import { SkeletonChart, SkeletonCard } from '../components/utils/Skeleton';
import { useWebSocket } from '../hooks/useWebSocket';

function formatTime(ts: string | null | undefined): string {
  if (!ts) return '-';
  return new Date(ts).toLocaleString();
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null) return '-';
  if (bytes < 1024) return `${bytes.toFixed(0)} B/s`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB/s`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB/s`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB/s`;
}

function formatUptime(bootTime: string | null | undefined): string {
  if (!bootTime) return '-';
  const boot = new Date(bootTime).getTime();
  const now = Date.now();
  const diffMs = now - boot;
  if (diffMs < 0) return '-';
  const days = Math.floor(diffMs / 86400000);
  const hours = Math.floor((diffMs % 86400000) / 3600000);
  const mins = Math.floor((diffMs % 3600000) / 60000);
  if (days > 0) return `${days}d ${hours}h ${mins}m`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

export default function HostDetails() {
  const { hostId } = useParams<{ hostId: string }>();
  const id = Number(hostId);
  const { data: host, isLoading, error } = useHostDetails(id);
  const [processModal, setProcessModal] = useState<'all' | 'zombie' | null>(null);

  // Live updates via WebSocket for this specific host
  const wsTopics = useMemo(() => [`host:${id}`, 'alerts'], [id]);
  useWebSocket(wsTopics);

  if (isLoading) return (
    <div>
      <div className="mb-6"><div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" /></div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
      <SkeletonChart />
    </div>
  );
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
          <div><span className="text-gray-500 dark:text-gray-400">Last Seen:</span> <span className="font-medium dark:text-gray-200">{host.last_seen_at ? <TimeAgo timestamp={host.last_seen_at} /> : '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Last Heartbeat:</span> <span className="font-medium dark:text-gray-200">{host.last_heartbeat_at ? <TimeAgo timestamp={host.last_heartbeat_at} /> : '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Metrics At:</span> <span className="font-medium dark:text-gray-200">{host.collected_at ? <TimeAgo timestamp={host.collected_at} /> : '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Registered:</span> <span className="font-medium dark:text-gray-200">{host.created_at ? <TimeAgo timestamp={host.created_at} /> : '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Active:</span> <span className="font-medium dark:text-gray-200">{host.is_active ? 'Yes' : 'No'}</span></div>
        </div>
      </div>

      {/* Gauge Charts */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col items-center">
          <GaugeChart value={host.cpu_percent ?? 0} label="CPU" />
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col items-center">
          <GaugeChart value={host.memory_percent ?? 0} label="Memory" />
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col items-center">
          <GaugeChart value={host.swap_percent ?? 0} label="Swap" />
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col items-center">
          <GaugeChart value={host.disk_percent_total ?? 0} label="Disk" />
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
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Swap Usage</p>
            <MetricBar value={host.swap_percent} />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Disk Usage (Total)</p>
            <MetricBar value={host.disk_percent_total} />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Load Average (1m)</p>
            <p className="text-lg font-semibold text-gray-800 dark:text-gray-100">{host.load_avg_1m?.toFixed(2) ?? '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Uptime</p>
            <p className="text-lg font-semibold text-gray-800 dark:text-gray-100">{formatUptime(host.boot_time)}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500">Boot: {formatTime(host.boot_time)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Processes</p>
            <button
              onClick={() => setProcessModal('all')}
              className="text-lg font-semibold text-blue-600 dark:text-blue-400 hover:underline cursor-pointer"
              title="View process list"
            >
              {host.process_count ?? '-'}
            </button>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Zombie Processes</p>
            <button
              onClick={() => setProcessModal('zombie')}
              className={`text-lg font-semibold hover:underline cursor-pointer ${(host.zombie_count ?? 0) > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-blue-600 dark:text-blue-400'}`}
              title="View zombie processes"
            >
              {host.zombie_count ?? '-'}
            </button>
          </div>
        </div>
      </div>

      {/* I/O & File Descriptors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Disk I/O */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Disk I/O</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">Read</span><span className="font-medium dark:text-gray-200">{formatBytes(host.disk_read_bytes_sec)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">Write</span><span className="font-medium dark:text-gray-200">{formatBytes(host.disk_write_bytes_sec)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">Read IOPS</span><span className="font-medium dark:text-gray-200">{host.disk_read_iops?.toFixed(0) ?? '-'}</span></div>
            <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">Write IOPS</span><span className="font-medium dark:text-gray-200">{host.disk_write_iops?.toFixed(0) ?? '-'}</span></div>
          </div>
        </div>

        {/* Network I/O */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Network I/O</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">Sent</span><span className="font-medium dark:text-gray-200">{formatBytes(host.net_bytes_sent_sec)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">Received</span><span className="font-medium dark:text-gray-200">{formatBytes(host.net_bytes_recv_sec)}</span></div>
          </div>
        </div>

        {/* File Descriptors */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">File Descriptors</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">Open</span><span className="font-medium dark:text-gray-200">{host.open_fds ?? '-'}</span></div>
            <div className="flex justify-between"><span className="text-gray-500 dark:text-gray-400">Max</span><span className="font-medium dark:text-gray-200">{host.max_fds ?? '-'}</span></div>
            {host.open_fds != null && host.max_fds != null && host.max_fds > 0 && (
              <div>
                <p className="text-gray-500 dark:text-gray-400 mb-1">Usage</p>
                <MetricBar value={Math.round((host.open_fds / host.max_fds) * 100)} />
              </div>
            )}
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
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Disk Usage</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Inode Usage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {host.mounts.map((m, i) => (
                  <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-2 text-sm font-mono text-gray-700 dark:text-gray-300">{m.mount_path}</td>
                    <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{m.total_gb?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{m.used_gb?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-2"><MetricBar value={m.used_percent} /></td>
                    <td className="px-4 py-2"><MetricBar value={m.inode_percent} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent History — Line Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Metric Trend</h2>
        {host.recent_history.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">No history available.</p>
        ) : (
          <MetricLineChart data={host.recent_history} />
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
                  {a.triggered_at && <TimeAgo timestamp={a.triggered_at} className="text-xs text-gray-400 dark:text-gray-500 ml-2" />}
                </div>
                <SeverityBadge severity={a.severity} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Process List Modal */}
      {processModal && (
        <ProcessListModal
          hostId={id}
          filter={processModal}
          onClose={() => setProcessModal(null)}
        />
      )}
    </div>
  );
}
