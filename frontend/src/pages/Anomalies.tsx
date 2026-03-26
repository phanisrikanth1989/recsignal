import { useState } from 'react';
import { useAnomalies, useAnomalySummary } from '../hooks/useApm';

export default function Anomalies() {
  const [statusFilter, setStatusFilter] = useState('');
  const { data: summary } = useAnomalySummary();
  const { data: anomalies, isLoading } = useAnomalies(undefined, statusFilter || undefined);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Anomaly Detection</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Dynamic baseline deviations across hosts</p>
        </div>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="">All Status</option>
          <option value="OPEN">Open</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </div>

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-xs text-gray-500 dark:text-gray-400">Total Anomalies</p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">{summary.total_anomalies}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-xs text-gray-500 dark:text-gray-400">Open</p>
            <p className="text-xl font-bold text-yellow-600 dark:text-yellow-400">{summary.open_anomalies}</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800 p-4">
            <p className="text-xs text-yellow-600 dark:text-yellow-400">Warning</p>
            <p className="text-xl font-bold text-yellow-700 dark:text-yellow-300">{summary.warning_count}</p>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 p-4">
            <p className="text-xs text-red-600 dark:text-red-400">Critical</p>
            <p className="text-xl font-bold text-red-700 dark:text-red-300">{summary.critical_count}</p>
          </div>
        </div>
      )}

      {/* Anomaly Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading anomalies...</div>
        ) : !anomalies || anomalies.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            No anomalies detected. Baselines are computed automatically as metric history accumulates.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Host</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Metric</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Observed</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Baseline</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Deviation</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Severity</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Detected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {anomalies.map(a => (
                  <tr key={a.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{a.hostname || `Host #${a.host_id}`}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 font-mono">{a.metric_name}</td>
                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">{a.observed_value.toFixed(1)}</td>
                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-500 dark:text-gray-400">
                      {a.baseline_mean.toFixed(1)} ± {a.baseline_stddev.toFixed(1)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-semibold">
                      <span className={a.deviation_sigma >= 3 ? 'text-red-600' : 'text-yellow-600'}>
                        {a.deviation_sigma.toFixed(1)}σ
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                        a.severity === 'critical'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                          : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                      }`}>{a.severity}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                        a.status === 'OPEN'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                          : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                      }`}>{a.status}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {new Date(a.detected_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
