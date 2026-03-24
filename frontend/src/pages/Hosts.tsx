import { Link, useSearchParams } from 'react-router-dom';
import { useHosts } from '../hooks/useHosts';
import StatusBadge from '../components/status/StatusBadge';
import MetricBar from '../components/charts/MetricBar';
import { useWebSocket } from '../hooks/useWebSocket';

import { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useHosts } from '../hooks/useHosts';
import StatusBadge from '../components/status/StatusBadge';
import MetricBar from '../components/charts/MetricBar';
import { SkeletonTable } from '../components/utils/Skeleton';
import { TimeAgo } from '../components/utils/TimeAgo';
import { useWebSocket } from '../hooks/useWebSocket';
import type { HostListItem } from '../types/host';

type SortKey = 'hostname' | 'cpu_percent' | 'memory_percent' | 'disk_percent_total' | 'status';
type SortDir = 'asc' | 'desc';

function exportCSV(hosts: HostListItem[]) {
  const header = 'Hostname,Environment,IP,CPU%,Memory%,Disk%,Status,Last Heartbeat';
  const rows = hosts.map(h =>
    [h.hostname, h.environment ?? '', h.ip_address ?? '', h.cpu_percent ?? '', h.memory_percent ?? '', h.disk_percent_total ?? '', h.status, h.last_heartbeat_at ?? ''].join(',')
  );
  const blob = new Blob([header + '\n' + rows.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `hosts-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

const STATUS_OPTIONS = ['all', 'healthy', 'warning', 'critical', 'stale'] as const;

export default function Hosts() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get('status') || 'all';
  const { data: hosts, isLoading, error } = useHosts();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('hostname');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  // Live updates via WebSocket
  useWebSocket(['hosts']);

  const allHosts = hosts || [];

  const filteredAndSorted = useMemo(() => {
    let list = statusFilter === 'all' ? allHosts : allHosts.filter(h => h.status === statusFilter);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(h =>
        h.hostname.toLowerCase().includes(q) ||
        (h.ip_address ?? '').toLowerCase().includes(q) ||
        (h.environment ?? '').toLowerCase().includes(q)
      );
    }
    return [...list].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number);
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [allHosts, statusFilter, search, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <span className="text-gray-300 dark:text-gray-600 ml-1">↕</span>;
    return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  if (isLoading) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Hosts</h1>
      <SkeletonTable rows={8} cols={7} />
    </div>
  );
  if (error) return <div className="text-center py-12 text-red-500 dark:text-red-400">Failed to load hosts.</div>;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Hosts {statusFilter !== 'all' && <span className="text-base font-normal text-gray-500 dark:text-gray-400 capitalize">— {statusFilter}</span>}
        </h1>
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <svg className="absolute left-2.5 top-2.5 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search hosts..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 w-56"
            />
          </div>
          {/* CSV Export */}
          <button
            onClick={() => exportCSV(filteredAndSorted)}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            title="Export to CSV"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            CSV
          </button>
        </div>
      </div>

      {/* Status Filter */}
      <div className="flex flex-wrap gap-2 mb-4">
        {STATUS_OPTIONS.map((s) => (
          <button
            key={s}
            onClick={() => s === 'all' ? setSearchParams({}) : setSearchParams({ status: s })}
            className={`px-3 py-1.5 text-sm rounded-md capitalize transition-colors ${
              statusFilter === s
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {s} {s !== 'all' ? `(${allHosts.filter((h) => h.status === s).length})` : `(${allHosts.length})`}
          </button>
        ))}
      </div>

      {/* Mobile / small screen card layout */}
      <div className="md:hidden space-y-3">
        {filteredAndSorted.map((h) => (
          <Link key={h.id} to={`/hosts/${h.id}`} className="block bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{h.hostname}</span>
              <StatusBadge status={h.status} />
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div><span className="text-gray-500 dark:text-gray-400">CPU</span><MetricBar value={h.cpu_percent} /></div>
              <div><span className="text-gray-500 dark:text-gray-400">Mem</span><MetricBar value={h.memory_percent} /></div>
              <div><span className="text-gray-500 dark:text-gray-400">Disk</span><MetricBar value={h.disk_percent_total} /></div>
            </div>
            {h.last_heartbeat_at && (
              <div className="mt-2"><TimeAgo timestamp={h.last_heartbeat_at} className="text-xs text-gray-400 dark:text-gray-500" /></div>
            )}
          </Link>
        ))}
      </div>

      {/* Desktop table */}
      <div className="hidden md:block bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('hostname')}>Hostname <SortIcon col="hostname" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Environment</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">IP Address</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('cpu_percent')}>CPU <SortIcon col="cpu_percent" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('memory_percent')}>Memory <SortIcon col="memory_percent" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('disk_percent_total')}>Disk <SortIcon col="disk_percent_total" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('status')}>Status <SortIcon col="status" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Last Heartbeat</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Details</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAndSorted.map((h) => (
                <tr key={h.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">{h.hostname}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{h.environment ?? '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{h.ip_address ?? '-'}</td>
                  <td className="px-4 py-3"><MetricBar value={h.cpu_percent} /></td>
                  <td className="px-4 py-3"><MetricBar value={h.memory_percent} /></td>
                  <td className="px-4 py-3"><MetricBar value={h.disk_percent_total} /></td>
                  <td className="px-4 py-3"><StatusBadge status={h.status} /></td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {h.last_heartbeat_at ? <TimeAgo timestamp={h.last_heartbeat_at} /> : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/hosts/${h.id}`}
                      className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 text-sm font-medium"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
              {filteredAndSorted.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                    {search ? 'No hosts match your search.' : 'No hosts registered yet.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
