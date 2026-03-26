import { useEffect, useState } from 'react';
import { fetchDbSessions } from '../../api/db_monitor';
import type { DbSessionItem } from '../../types/db_monitor';

interface SessionListModalProps {
  instanceId: number;
  instanceName: string;
  filter?: 'all' | 'ACTIVE' | 'INACTIVE';
  onClose: () => void;
}

export default function SessionListModal({ instanceId, instanceName, filter = 'all', onClose }: SessionListModalProps) {
  const [sessions, setSessions] = useState<DbSessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState(filter);

  useEffect(() => {
    setLoading(true);
    const statusFilter = activeFilter === 'all' ? undefined : activeFilter;
    fetchDbSessions(instanceId, statusFilter)
      .then(setSessions)
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, [instanceId, activeFilter]);

  const filters = [
    { key: 'all' as const, label: 'All' },
    { key: 'ACTIVE' as const, label: 'Active' },
    { key: 'INACTIVE' as const, label: 'Inactive' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-6xl max-h-[80vh] flex flex-col mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
            Sessions — {instanceName}
          </h2>
          <div className="flex items-center gap-3">
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
              {filters.map(f => (
                <button
                  key={f.key}
                  onClick={() => setActiveFilter(f.key)}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    activeFilter === f.key
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl leading-none"
            >
              &times;
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="overflow-auto flex-1 p-4">
          {loading ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">Loading sessions...</p>
          ) : sessions.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">No sessions found.</p>
          ) : (
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/50 sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">SID</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Serial#</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">User</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Program</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Machine</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">SQL ID</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Wait Event</th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Wait (s)</th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Elapsed (s)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-3 py-2 text-sm font-mono text-gray-700 dark:text-gray-300">{s.sid ?? '-'}</td>
                    <td className="px-3 py-2 text-sm font-mono text-gray-700 dark:text-gray-300">{s.serial_no ?? '-'}</td>
                    <td className="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">{s.username ?? '-'}</td>
                    <td className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 truncate max-w-[150px]" title={s.program ?? ''}>{s.program ?? '-'}</td>
                    <td className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400">{s.machine ?? '-'}</td>
                    <td className="px-3 py-2 text-sm">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        s.status === 'ACTIVE'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                      }`}>
                        {s.status ?? '-'}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-sm font-mono text-gray-600 dark:text-gray-400">{s.sql_id ?? '-'}</td>
                    <td className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 truncate max-w-[150px]" title={s.wait_event ?? ''}>{s.wait_event ?? '-'}</td>
                    <td className="px-3 py-2 text-sm text-right text-gray-700 dark:text-gray-300">{s.seconds_in_wait?.toFixed(0) ?? '-'}</td>
                    <td className="px-3 py-2 text-sm text-right text-gray-700 dark:text-gray-300">{s.elapsed_seconds?.toFixed(0) ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-400 dark:text-gray-500">
          {sessions.length} session{sessions.length !== 1 ? 's' : ''} shown
        </div>
      </div>
    </div>
  );
}
