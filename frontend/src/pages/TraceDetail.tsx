import { useParams } from 'react-router-dom';
import { useTraceDetail } from '../hooks/useApm';
import type { SpanItem } from '../types/apm';

function SpanBar({ span, traceStart, traceDuration }: { span: SpanItem; traceStart: number; traceDuration: number }) {
  const spanStart = new Date(span.started_at).getTime();
  const leftPct = traceDuration > 0 ? ((spanStart - traceStart) / traceDuration) * 100 : 0;
  const widthPct = traceDuration > 0 ? Math.max((span.duration_ms / traceDuration) * 100, 0.5) : 100;

  const colors: Record<string, string> = {
    server: 'bg-blue-500',
    client: 'bg-green-500',
    internal: 'bg-indigo-500',
    producer: 'bg-purple-500',
    consumer: 'bg-yellow-500',
  };

  return (
    <div className="flex items-center gap-3 py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
      <div className="w-48 flex-shrink-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={span.operation_name}>
          {span.operation_name}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{span.service_name}</p>
      </div>
      <div className="flex-1 h-6 bg-gray-100 dark:bg-gray-700 rounded relative">
        <div
          className={`absolute top-0 h-full rounded ${span.status === 'error' ? 'bg-red-500' : colors[span.span_kind] || 'bg-indigo-500'}`}
          style={{ left: `${Math.min(leftPct, 99)}%`, width: `${Math.min(widthPct, 100 - leftPct)}%` }}
          title={`${span.duration_ms.toFixed(1)} ms`}
        />
      </div>
      <div className="w-20 flex-shrink-0 text-right">
        <span className={`text-xs font-mono ${span.status === 'error' ? 'text-red-600' : 'text-gray-600 dark:text-gray-400'}`}>
          {span.duration_ms.toFixed(1)} ms
        </span>
      </div>
    </div>
  );
}

export default function TraceDetail() {
  const { traceId } = useParams<{ traceId: string }>();
  const { data: trace, isLoading } = useTraceDetail(traceId || '');

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading trace...</div>;
  if (!trace) return <div className="p-8 text-center text-red-500">Trace not found</div>;

  const traceStart = new Date(trace.started_at).getTime();
  const traceDuration = trace.total_duration_ms;

  // Build tree order from spans
  const sortedSpans = [...(trace.spans || [])].sort((a, b) =>
    new Date(a.started_at).getTime() - new Date(b.started_at).getTime()
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Trace Detail</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 font-mono">{trace.trace_id}</p>
      </div>

      {/* Trace Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Service</p>
          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-1">{trace.root_service}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Endpoint</p>
          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-1 truncate">
            {trace.root_method} {trace.root_endpoint}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Duration</p>
          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-1">{trace.total_duration_ms.toFixed(1)} ms</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Spans</p>
          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-1">{trace.span_count}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Status</p>
          <p className={`text-sm font-semibold mt-1 ${trace.has_error ? 'text-red-600' : 'text-green-600 dark:text-green-400'}`}>
            {trace.has_error ? 'Error' : 'OK'} {trace.status_code ? `(${trace.status_code})` : ''}
          </p>
        </div>
      </div>

      {/* Waterfall View */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Span Waterfall</h2>
        <div className="flex items-center gap-3 mb-3 text-xs text-gray-400">
          <span className="w-48 flex-shrink-0">Operation</span>
          <span className="flex-1 flex justify-between">
            <span>0 ms</span>
            <span>{(traceDuration / 4).toFixed(0)} ms</span>
            <span>{(traceDuration / 2).toFixed(0)} ms</span>
            <span>{((traceDuration * 3) / 4).toFixed(0)} ms</span>
            <span>{traceDuration.toFixed(0)} ms</span>
          </span>
          <span className="w-20 flex-shrink-0 text-right">Duration</span>
        </div>
        {sortedSpans.length === 0 ? (
          <p className="text-sm text-gray-500">No spans in this trace.</p>
        ) : (
          sortedSpans.map(span => (
            <SpanBar key={span.span_id} span={span} traceStart={traceStart} traceDuration={traceDuration} />
          ))
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-500 inline-block" /> Server</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-500 inline-block" /> Client</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-indigo-500 inline-block" /> Internal</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500 inline-block" /> Error</span>
      </div>
    </div>
  );
}
