import { useParams, Link } from 'react-router-dom';
import { useDbInstanceDetail } from '../hooks/useDbMonitor';
import { useWebSocket } from '../hooks/useWebSocket';
import StatusBadge from '../components/status/StatusBadge';
import MetricBar from '../components/charts/MetricBar';
import GaugeChart from '../components/charts/GaugeChart';
import { SkeletonCard } from '../components/utils/Skeleton';

function formatUptime(seconds: number | null | undefined): string {
  if (!seconds) return '-';
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${d}d ${h}h ${m}m`;
}

function formatMB(mb: number | null | undefined): string {
  if (mb == null) return '-';
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${mb.toFixed(0)} MB`;
}

function truncateSql(sql: string | null | undefined, maxLen = 120): string {
  if (!sql) return '-';
  return sql.length > maxLen ? sql.slice(0, maxLen) + '…' : sql;
}

export default function DbInstanceDetails() {
  const { instanceId } = useParams();
  const id = instanceId ? parseInt(instanceId, 10) : null;
  const { data: instance, isLoading, error } = useDbInstanceDetail(id);

  // Live updates via WebSocket
  useWebSocket(id ? [`db-instance:${id}`, 'db-monitor-summary'] : []);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">DB Instance</h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error || !instance) {
    return <div className="text-center py-12 text-red-500">Failed to load DB instance details.</div>;
  }

  const perf = instance.performance;
  const sess = instance.sessions_summary;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{instance.instance_name}</h1>
          <span className="text-sm text-gray-500 dark:text-gray-400 uppercase">{instance.db_type}</span>
        </div>
        <StatusBadge status={instance.status} />
      </div>

      {/* Instance Info */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Instance Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-gray-500 dark:text-gray-400">Host:</span> <span className="font-medium dark:text-gray-200">{instance.host ?? '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Port:</span> <span className="font-medium dark:text-gray-200">{instance.port ?? '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Service:</span> <span className="font-medium dark:text-gray-200">{instance.service_name ?? '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Environment:</span> <span className="font-medium dark:text-gray-200">{instance.environment ?? '-'}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Uptime:</span> <span className="font-medium dark:text-gray-200">{formatUptime(perf?.db_uptime_seconds)}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">SGA:</span> <span className="font-medium dark:text-gray-200">{formatMB(perf?.sga_total_mb)}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">PGA:</span> <span className="font-medium dark:text-gray-200">{formatMB(perf?.pga_total_mb)}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">Support Group:</span> <span className="font-medium dark:text-gray-200">{instance.support_group ?? '-'}</span></div>
        </div>
      </div>

      {/* Gauge Charts */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col items-center">
          <GaugeChart value={perf?.buffer_cache_hit_ratio ?? null} label="Buffer Cache Hit" />
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col items-center">
          <GaugeChart value={perf?.library_cache_hit_ratio ?? null} label="Library Cache Hit" />
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col items-center">
          <GaugeChart value={perf ? (perf.active_sessions && perf.max_sessions ? (perf.active_sessions / perf.max_sessions) * 100 : 0) : null} label="Session Utilization" />
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col items-center text-center">
          <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{sess?.active ?? 0}</div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Active Sessions</p>
          <p className="text-xs text-gray-400 dark:text-gray-500">{sess?.total ?? 0} total / {sess?.blocking_count ?? 0} blocking</p>
        </div>
      </div>

      {/* Performance Metrics */}
      {perf && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Performance Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><span className="text-gray-500 dark:text-gray-400">Execute Count:</span> <span className="font-bold text-gray-900 dark:text-gray-100">{perf.execute_count?.toLocaleString() ?? '-'}</span></div>
            <div><span className="text-gray-500 dark:text-gray-400">Parse Count:</span> <span className="font-bold text-gray-900 dark:text-gray-100">{perf.parse_count_total?.toLocaleString() ?? '-'}</span></div>
            <div><span className="text-gray-500 dark:text-gray-400">Hard Parses:</span> <span className="font-bold text-gray-900 dark:text-gray-100">{perf.hard_parse_count?.toLocaleString() ?? '-'}</span></div>
            <div><span className="text-gray-500 dark:text-gray-400">Physical Reads:</span> <span className="font-bold text-gray-900 dark:text-gray-100">{perf.physical_reads?.toLocaleString() ?? '-'}</span></div>
            <div><span className="text-gray-500 dark:text-gray-400">Physical Writes:</span> <span className="font-bold text-gray-900 dark:text-gray-100">{perf.physical_writes?.toLocaleString() ?? '-'}</span></div>
            <div><span className="text-gray-500 dark:text-gray-400">Commits:</span> <span className="font-bold text-gray-900 dark:text-gray-100">{perf.user_commits?.toLocaleString() ?? '-'}</span></div>
            <div><span className="text-gray-500 dark:text-gray-400">Rollbacks:</span> <span className="font-bold text-gray-900 dark:text-gray-100">{perf.user_rollbacks?.toLocaleString() ?? '-'}</span></div>
            <div><span className="text-gray-500 dark:text-gray-400">Redo Size:</span> <span className="font-bold text-gray-900 dark:text-gray-100">{perf.redo_size?.toLocaleString() ?? '-'}</span></div>
          </div>
        </div>
      )}

      {/* Tablespace Usage */}
      {instance.tablespaces.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Tablespace Usage</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tablespace</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Usage</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Used</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Total</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Free</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Auto Ext</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {instance.tablespaces.map((ts) => (
                  <tr key={ts.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-100">{ts.tablespace_name}</td>
                    <td className="px-4 py-2 min-w-[180px]"><MetricBar value={ts.used_percent} /></td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600 dark:text-gray-400">{formatMB(ts.used_mb)}</td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600 dark:text-gray-400">{formatMB(ts.total_mb)}</td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600 dark:text-gray-400">{formatMB(ts.free_mb)}</td>
                    <td className="px-4 py-2 text-sm text-center text-gray-600 dark:text-gray-400">{ts.autoextensible ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-center">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ts.status === 'ONLINE' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>
                        {ts.status ?? '-'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Sessions Summary */}
      {sess && sess.total > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Sessions Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{sess.total}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Total</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">{sess.active}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Active</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-500 dark:text-gray-400">{sess.inactive}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Inactive</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${sess.blocking_count > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>{sess.blocking_count}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Blocking</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${sess.long_running_count > 0 ? 'text-yellow-600 dark:text-yellow-400' : 'text-gray-500 dark:text-gray-400'}`}>{sess.long_running_count}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Long Running</div>
            </div>
          </div>
        </div>
      )}

      {/* Slow Queries */}
      {instance.slow_queries.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Top Slow Queries</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">SQL ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">SQL Text</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">User</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Elapsed (s)</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">CPU (s)</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Buffer Gets</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Disk Reads</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Executions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {instance.slow_queries.map((q) => (
                  <tr key={q.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-2 text-sm font-mono text-gray-900 dark:text-gray-100">{q.sql_id ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 max-w-xs truncate" title={q.sql_text ?? ''}>{truncateSql(q.sql_text)}</td>
                    <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{q.username ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-right font-medium text-gray-900 dark:text-gray-100">{q.elapsed_seconds?.toFixed(2) ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600 dark:text-gray-400">{q.cpu_seconds?.toFixed(2) ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600 dark:text-gray-400">{q.buffer_gets?.toLocaleString() ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600 dark:text-gray-400">{q.disk_reads?.toLocaleString() ?? '-'}</td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600 dark:text-gray-400">{q.executions?.toLocaleString() ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
