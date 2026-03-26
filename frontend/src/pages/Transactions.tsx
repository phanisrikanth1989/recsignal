import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTransactions, useAppNames } from '../hooks/useApm';

export default function Transactions() {
  const [searchParams] = useSearchParams();
  const initialApp = searchParams.get('app') || '';
  const [selectedApp, setSelectedApp] = useState(initialApp);

  const { data: appNames } = useAppNames();
  const { data: transactions, isLoading } = useTransactions(selectedApp || undefined);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Business Transactions</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Monitor request throughput, latency, and errors</p>
        </div>
        <select
          value={selectedApp}
          onChange={e => setSelectedApp(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="">All Applications</option>
          {appNames?.map(name => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading transactions...</div>
        ) : !transactions || transactions.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">No transactions recorded yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Endpoint</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Method</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">App</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Response Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Trace</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {transactions.map(tx => (
                  <tr key={tx.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-4 py-3 text-sm font-mono text-gray-900 dark:text-white truncate max-w-xs">{tx.endpoint}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                        tx.method === 'GET' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                        tx.method === 'POST' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                        tx.method === 'PUT' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        tx.method === 'DELETE' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}>{tx.method}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{tx.app_name}</td>
                    <td className="px-4 py-3 text-sm text-right">
                      <span className={tx.is_error ? 'text-red-600 font-semibold' : 'text-green-600 dark:text-green-400'}>
                        {tx.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      <span className={tx.response_time_ms > 1000 ? 'text-red-600 font-semibold' : tx.response_time_ms > 500 ? 'text-yellow-600' : 'text-gray-700 dark:text-gray-300'}>
                        {tx.response_time_ms.toFixed(1)} ms
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {tx.trace_id ? (
                        <Link to={`/apm/traces/${tx.trace_id}`} className="text-indigo-600 dark:text-indigo-400 hover:underline font-mono text-xs">
                          {tx.trace_id.slice(0, 8)}...
                        </Link>
                      ) : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {new Date(tx.collected_at).toLocaleString()}
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
