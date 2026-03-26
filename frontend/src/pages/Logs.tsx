import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLogs, useLogSummary, useLogSources } from '../hooks/useApm';

const LEVEL_STYLES: Record<string, string> = {
  ERROR: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  FATAL: 'bg-red-200 text-red-900 dark:bg-red-900/50 dark:text-red-300',
  WARN: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  INFO: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  DEBUG: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

export default function Logs() {
  const [searchQuery, setSearchQuery] = useState('');
  const [level, setLevel] = useState('');
  const [source, setSource] = useState('');

  const { data: summary } = useLogSummary();
  const { data: sources } = useLogSources();
  const { data: result, isLoading } = useLogs(
    searchQuery || undefined,
    undefined,
    level || undefined,
    source || undefined,
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Log Analytics</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Search, filter, and analyze application logs</p>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-xs text-gray-500 dark:text-gray-400">Total Logs</p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">{summary.total_logs.toLocaleString()}</p>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 p-4">
            <p className="text-xs text-red-600 dark:text-red-400">Errors</p>
            <p className="text-xl font-bold text-red-700 dark:text-red-300">{summary.error_count}</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800 p-4">
            <p className="text-xs text-yellow-600 dark:text-yellow-400">Warnings</p>
            <p className="text-xl font-bold text-yellow-700 dark:text-yellow-300">{summary.warn_count}</p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 p-4">
            <p className="text-xs text-blue-600 dark:text-blue-400">Info</p>
            <p className="text-xl font-bold text-blue-700 dark:text-blue-300">{summary.info_count}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Search logs..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="flex-1 px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400"
        />
        <select
          value={level}
          onChange={e => setLevel(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="">All Levels</option>
          <option value="FATAL">FATAL</option>
          <option value="ERROR">ERROR</option>
          <option value="WARN">WARN</option>
          <option value="INFO">INFO</option>
          <option value="DEBUG">DEBUG</option>
        </select>
        <select
          value={source}
          onChange={e => setSource(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="">All Sources</option>
          {sources?.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Log Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {result && <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-700 text-xs text-gray-500">{result.total} results</div>}
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Searching...</div>
        ) : !result || result.logs.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">No logs found.</div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
            {result.logs.map(log => (
              <div key={log.id} className="px-6 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded flex-shrink-0 ${LEVEL_STYLES[log.level] || LEVEL_STYLES.INFO}`}>
                    {log.level}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0 whitespace-nowrap">
                    {new Date(log.logged_at).toLocaleString()}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">{log.hostname}</span>
                  <span className="text-xs text-indigo-500 dark:text-indigo-400 flex-shrink-0 truncate max-w-[150px]">{log.source}</span>
                  {log.trace_id && (
                    <Link to={`/apm/traces/${log.trace_id}`} className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-mono flex-shrink-0">
                      {log.trace_id.slice(0, 8)}
                    </Link>
                  )}
                </div>
                <p className="text-sm text-gray-900 dark:text-white mt-1 font-mono whitespace-pre-wrap break-all">{log.message}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
