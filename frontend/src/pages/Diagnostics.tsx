import { useState } from 'react';
import { useDiagnostics } from '../hooks/useApm';

function JsonViewer({ jsonStr }: { jsonStr: string | null }) {
  if (!jsonStr) return <span className="text-gray-400">—</span>;
  try {
    const parsed = JSON.parse(jsonStr);
    return (
      <pre className="text-xs font-mono bg-gray-50 dark:bg-gray-900 p-3 rounded-lg overflow-x-auto max-h-60 overflow-y-auto text-gray-700 dark:text-gray-300">
        {JSON.stringify(parsed, null, 2)}
      </pre>
    );
  } catch {
    return <pre className="text-xs font-mono text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{jsonStr}</pre>;
  }
}

const SNAPSHOT_TYPES = ['cpu_profile', 'memory_profile', 'thread_dump'];

export default function Diagnostics() {
  const [selectedType, setSelectedType] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data: snapshots, isLoading } = useDiagnostics(undefined, selectedType || undefined);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Code-Level Diagnostics</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">CPU profiles, memory snapshots, and thread dumps</p>
        </div>
        <select
          value={selectedType}
          onChange={e => setSelectedType(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="">All Types</option>
          {SNAPSHOT_TYPES.map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
        </select>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading diagnostics...</div>
        ) : !snapshots || snapshots.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">No diagnostic snapshots yet.</div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {snapshots.map(snap => (
              <div key={snap.id}>
                <div
                  className="px-6 py-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/30 flex items-center justify-between"
                  onClick={() => setExpandedId(expandedId === snap.id ? null : snap.id)}
                >
                  <div className="flex items-center gap-4">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      snap.snapshot_type === 'cpu_profile' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                      snap.snapshot_type === 'memory_profile' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400' :
                      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                    }`}>
                      {snap.snapshot_type.replace('_', ' ')}
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">{snap.app_name}</span>
                    {snap.duration_seconds !== null && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">{snap.duration_seconds.toFixed(1)}s</span>
                    )}
                    {snap.triggered_by && (
                      <span className="text-xs text-gray-400 dark:text-gray-500">by {snap.triggered_by}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {new Date(snap.collected_at).toLocaleString()}
                    </span>
                    <svg className={`w-4 h-4 text-gray-400 transition-transform ${expandedId === snap.id ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
                {expandedId === snap.id && (
                  <div className="px-6 pb-4 space-y-3">
                    {snap.top_functions && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Top Functions</h4>
                        <JsonViewer jsonStr={snap.top_functions} />
                      </div>
                    )}
                    {snap.memory_summary && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Memory Summary</h4>
                        <JsonViewer jsonStr={snap.memory_summary} />
                      </div>
                    )}
                    {snap.thread_dump && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Thread Dump</h4>
                        <JsonViewer jsonStr={snap.thread_dump} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
