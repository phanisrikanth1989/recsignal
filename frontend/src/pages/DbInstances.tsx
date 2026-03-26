import { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useDbInstances } from '../hooks/useDbMonitor';
import StatusBadge from '../components/status/StatusBadge';
import { SkeletonTable } from '../components/utils/Skeleton';
import { TimeAgo } from '../components/utils/TimeAgo';
import type { DbInstanceListItem } from '../types/db_monitor';

type SortKey = 'instance_name' | 'db_type' | 'host' | 'environment' | 'status';
type SortDir = 'asc' | 'desc';

function exportCSV(instances: DbInstanceListItem[]) {
  const header = 'Instance,Type,Host,Port,Service,Environment,Status,Last Seen';
  const rows = instances.map(i =>
    [i.instance_name, i.db_type, i.host ?? '', i.port ?? '', i.service_name ?? '', i.environment ?? '', i.status, i.last_seen_at ?? ''].join(',')
  );
  const blob = new Blob([header + '\n' + rows.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `db-instances-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

const STATUS_OPTIONS = ['all', 'up', 'degraded', 'down', 'unknown'] as const;

export default function DbInstances() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get('status') || 'all';
  const { data: instances, isLoading, error } = useDbInstances();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('instance_name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const allInstances = instances || [];

  const filteredAndSorted = useMemo(() => {
    let list = statusFilter === 'all' ? allInstances : allInstances.filter(i => i.status === statusFilter);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(i =>
        i.instance_name.toLowerCase().includes(q) ||
        (i.host ?? '').toLowerCase().includes(q) ||
        (i.environment ?? '').toLowerCase().includes(q) ||
        (i.service_name ?? '').toLowerCase().includes(q)
      );
    }
    return [...list].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [allInstances, statusFilter, search, sortKey, sortDir]);

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
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Database Instances</h1>
      <SkeletonTable rows={8} cols={7} />
    </div>
  );
  if (error) return <div className="text-center py-12 text-red-500 dark:text-red-400">Failed to load database instances.</div>;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Database Instances {statusFilter !== 'all' && <span className="text-base font-normal text-gray-500 dark:text-gray-400 capitalize">— {statusFilter}</span>}
        </h1>
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <svg className="absolute left-2.5 top-2.5 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search instances..."
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
            {s} {s !== 'all' ? `(${allInstances.filter((i) => i.status === s).length})` : `(${allInstances.length})`}
          </button>
        ))}
      </div>

      {/* Mobile card layout */}
      <div className="md:hidden space-y-3">
        {filteredAndSorted.map((inst) => (
          <Link key={inst.id} to={`/db-instances/${inst.id}`} className="block bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{inst.instance_name}</span>
              <StatusBadge status={inst.status} />
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs text-gray-500 dark:text-gray-400">
              <div><span className="block mb-0.5">Type</span><span className="font-medium text-gray-700 dark:text-gray-300 uppercase">{inst.db_type}</span></div>
              <div><span className="block mb-0.5">Host</span><span className="font-medium text-gray-700 dark:text-gray-300">{inst.host ?? '-'}:{inst.port ?? '-'}</span></div>
              <div><span className="block mb-0.5">Env</span><span className="font-medium text-gray-700 dark:text-gray-300">{inst.environment ?? '-'}</span></div>
            </div>
            {inst.last_seen_at && (
              <div className="mt-2"><TimeAgo timestamp={inst.last_seen_at} className="text-xs text-gray-400 dark:text-gray-500" /></div>
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
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('instance_name')}>Instance <SortIcon col="instance_name" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('db_type')}>Type <SortIcon col="db_type" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('host')}>Host <SortIcon col="host" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Service</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('environment')}>Environment <SortIcon col="environment" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase cursor-pointer select-none" onClick={() => toggleSort('status')}>Status <SortIcon col="status" /></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Last Seen</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Details</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAndSorted.map((inst) => (
                <tr key={inst.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">{inst.instance_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 uppercase">{inst.db_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{inst.host ?? '-'}:{inst.port ?? '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{inst.service_name ?? '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{inst.environment ?? '-'}</td>
                  <td className="px-4 py-3"><StatusBadge status={inst.status} /></td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {inst.last_seen_at ? <TimeAgo timestamp={inst.last_seen_at} /> : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/db-instances/${inst.id}`}
                      className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 text-sm font-medium"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
              {filteredAndSorted.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                    {search ? 'No instances match your search.' : 'No database instances registered yet.'}
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
