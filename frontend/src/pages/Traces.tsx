import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTraces, useServices } from '../hooks/useApm';

export default function Traces() {
  const [selectedService, setSelectedService] = useState('');
  const [errorOnly, setErrorOnly] = useState(false);

  const { data: services } = useServices();
  const { data: traces, isLoading } = useTraces(
    selectedService || undefined,
    errorOnly ? true : undefined,
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Distributed Traces</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">End-to-end request tracing across services</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedService}
            onChange={e => setSelectedService(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="">All Services</option>
            {services?.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <input type="checkbox" checked={errorOnly} onChange={e => setErrorOnly(e.target.checked)} className="rounded" />
            Errors only
          </label>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading traces...</div>
        ) : !traces || traces.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">No traces recorded yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Trace ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Service</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Endpoint</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Duration</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Spans</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {traces.map(t => (
                  <tr key={t.trace_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-4 py-3">
                      <Link to={`/apm/traces/${t.trace_id}`} className="text-indigo-600 dark:text-indigo-400 hover:underline font-mono text-sm">
                        {t.trace_id.slice(0, 16)}...
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{t.root_service}</td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-600 dark:text-gray-400 truncate max-w-xs">
                      {t.root_method && <span className="font-bold mr-1">{t.root_method}</span>}
                      {t.root_endpoint || '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      <span className={t.total_duration_ms > 1000 ? 'text-red-600 font-semibold' : 'text-gray-700 dark:text-gray-300'}>
                        {t.total_duration_ms.toFixed(1)} ms
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{t.span_count}</td>
                    <td className="px-4 py-3 text-center">
                      {t.has_error ? (
                        <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">Error</span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">OK</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {new Date(t.started_at).toLocaleString()}
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
