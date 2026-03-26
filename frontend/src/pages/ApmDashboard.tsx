import { Link } from 'react-router-dom';
import { useBtSummary, useAnomalySummary, useLogSummary } from '../hooks/useApm';

function StatCard({ label, value, color = 'indigo', to }: { label: string; value: string | number; color?: string; to?: string }) {
  const colors: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
    red: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    yellow: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
    green: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    blue: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  };
  const card = (
    <div className={`rounded-xl p-5 ${colors[color] || colors.indigo} transition-shadow hover:shadow-md`}>
      <p className="text-sm font-medium opacity-75">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
  return to ? <Link to={to}>{card}</Link> : card;
}

export default function ApmDashboard() {
  const { data: btSummary, isLoading: btLoading } = useBtSummary();
  const { data: anomalySummary, isLoading: anomalyLoading } = useAnomalySummary();
  const { data: logSummary, isLoading: logLoading } = useLogSummary();

  const totalRequests = btSummary?.reduce((sum, s) => sum + s.total_requests, 0) ?? 0;
  const totalErrors = btSummary?.reduce((sum, s) => sum + s.error_count, 0) ?? 0;
  const avgResponseTime = btSummary && btSummary.length > 0
    ? Math.round(btSummary.reduce((sum, s) => sum + s.avg_response_time_ms, 0) / btSummary.length)
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">APM Dashboard</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Application Performance Monitoring overview</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard
          label="Total Requests"
          value={btLoading ? '...' : totalRequests.toLocaleString()}
          color="indigo"
          to="/apm/transactions"
        />
        <StatCard
          label="Avg Response Time"
          value={btLoading ? '...' : `${avgResponseTime} ms`}
          color="blue"
          to="/apm/transactions"
        />
        <StatCard
          label="Total Errors"
          value={btLoading ? '...' : totalErrors}
          color="red"
          to="/apm/transactions"
        />
        <StatCard
          label="Open Anomalies"
          value={anomalyLoading ? '...' : anomalySummary?.open_anomalies ?? 0}
          color={anomalySummary && anomalySummary.open_anomalies > 0 ? 'yellow' : 'green'}
          to="/apm/anomalies"
        />
        <StatCard
          label="Log Errors"
          value={logLoading ? '...' : logSummary?.error_count ?? 0}
          color={logSummary && logSummary.error_count > 0 ? 'red' : 'green'}
          to="/apm/logs"
        />
        <StatCard
          label="Total Logs"
          value={logLoading ? '...' : (logSummary?.total_logs ?? 0).toLocaleString()}
          color="blue"
          to="/apm/logs"
        />
      </div>

      {/* App Summaries Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Application Summary</h2>
        </div>
        {btLoading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : !btSummary || btSummary.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            No business transactions yet. Configure your agent to send APM data.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Application</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Requests</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Avg Response</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Errors</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Error Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {btSummary.map(app => (
                <tr key={app.app_name} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="px-6 py-4 text-sm font-medium text-indigo-600 dark:text-indigo-400">
                    <Link to={`/apm/transactions?app=${encodeURIComponent(app.app_name)}`}>{app.app_name}</Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-right text-gray-700 dark:text-gray-300">{app.total_requests.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-700 dark:text-gray-300">{app.avg_response_time_ms.toFixed(1)} ms</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-700 dark:text-gray-300">{app.error_count}</td>
                  <td className="px-6 py-4 text-sm text-right">
                    <span className={app.error_rate > 5 ? 'text-red-600 font-semibold' : 'text-gray-700 dark:text-gray-300'}>
                      {app.error_rate.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { to: '/apm/transactions', label: 'Transactions', desc: 'Business transaction details' },
          { to: '/apm/traces', label: 'Traces', desc: 'Distributed trace analysis' },
          { to: '/apm/topology', label: 'Service Map', desc: 'Service dependency flowmap' },
          { to: '/apm/logs', label: 'Log Analytics', desc: 'Search and filter logs' },
          { to: '/apm/anomalies', label: 'Anomalies', desc: 'Baseline deviations' },
          { to: '/apm/diagnostics', label: 'Diagnostics', desc: 'CPU/memory profiling' },
        ].map(item => (
          <Link
            key={item.to}
            to={item.to}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition-shadow"
          >
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{item.label}</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
