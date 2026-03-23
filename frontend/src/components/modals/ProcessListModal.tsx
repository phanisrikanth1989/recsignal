import { useEffect, useState } from 'react';
import { fetchProcesses } from '../../api/hosts';
import type { ProcessItem } from '../../types/host';

interface ProcessListModalProps {
  hostId: number;
  filter?: 'all' | 'zombie';
  onClose: () => void;
}

export default function ProcessListModal({ hostId, filter = 'all', onClose }: ProcessListModalProps) {
  const [processes, setProcesses] = useState<ProcessItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState(filter);

  useEffect(() => {
    setLoading(true);
    const statusFilter = activeFilter === 'zombie' ? 'zombie' : undefined;
    fetchProcesses(hostId, statusFilter)
      .then(setProcesses)
      .catch(() => setProcesses([]))
      .finally(() => setLoading(false));
  }, [hostId, activeFilter]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-4xl max-h-[80vh] flex flex-col mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
            Process List
          </h2>
          <div className="flex items-center gap-3">
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
              <button
                onClick={() => setActiveFilter('all')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  activeFilter === 'all'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setActiveFilter('zombie')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  activeFilter === 'zombie'
                    ? 'bg-amber-100 dark:bg-amber-900/50 text-amber-800 dark:text-amber-300 shadow-sm'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                }`}
              >
                Zombies
              </button>
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
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">Loading processes...</p>
          ) : processes.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              {activeFilter === 'zombie' ? 'No zombie processes found.' : 'No process data available.'}
            </p>
          ) : (
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/50 sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">PID</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Name</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">User</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">CPU %</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Mem %</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {processes.map((p) => (
                  <tr key={p.pid} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-3 py-2 text-sm font-mono text-gray-700 dark:text-gray-300">{p.pid}</td>
                    <td className="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">{p.name}</td>
                    <td className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400">{p.username}</td>
                    <td className="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">{p.cpu_percent.toFixed(1)}</td>
                    <td className="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">{p.memory_percent.toFixed(1)}</td>
                    <td className="px-3 py-2 text-sm">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        p.status === 'zombie'
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300'
                          : p.status === 'running'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400">
          <span>{processes.length} process{processes.length !== 1 ? 'es' : ''}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
