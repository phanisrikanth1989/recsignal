import { useTopology } from '../hooks/useApm';
import type { ServiceNodeItem, ServiceDependencyItem } from '../types/apm';

function getNodeColor(status: string) {
  switch (status) {
    case 'critical': return { bg: 'bg-red-100 dark:bg-red-900/30', border: 'border-red-500', text: 'text-red-700 dark:text-red-400' };
    case 'warning': return { bg: 'bg-yellow-100 dark:bg-yellow-900/30', border: 'border-yellow-500', text: 'text-yellow-700 dark:text-yellow-400' };
    default: return { bg: 'bg-green-100 dark:bg-green-900/30', border: 'border-green-500', text: 'text-green-700 dark:text-green-400' };
  }
}

function getTypeIcon(type: string) {
  switch (type) {
    case 'database': return '🗄️';
    case 'queue': return '📨';
    case 'external': return '🌐';
    default: return '🔷';
  }
}

function ServiceCard({ node }: { node: ServiceNodeItem }) {
  const colors = getNodeColor(node.status);
  return (
    <div className={`${colors.bg} ${colors.border} border-2 rounded-xl p-4 min-w-[200px] shadow-sm`}>
      <div className="flex items-center gap-2">
        <span className="text-lg">{getTypeIcon(node.service_type)}</span>
        <h3 className={`text-sm font-bold ${colors.text}`}>{node.service_name}</h3>
      </div>
      <div className="mt-2 space-y-1 text-xs text-gray-600 dark:text-gray-400">
        {node.avg_response_time_ms !== null && (
          <div className="flex justify-between">
            <span>Avg Response:</span>
            <span className="font-mono">{node.avg_response_time_ms.toFixed(1)} ms</span>
          </div>
        )}
        {node.request_rate !== null && (
          <div className="flex justify-between">
            <span>Request Rate:</span>
            <span className="font-mono">{node.request_rate.toFixed(1)} rpm</span>
          </div>
        )}
        {node.error_rate !== null && (
          <div className="flex justify-between">
            <span>Error Rate:</span>
            <span className={`font-mono ${node.error_rate > 5 ? 'text-red-600' : ''}`}>{node.error_rate.toFixed(1)}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

function EdgeLabel({ edge }: { edge: ServiceDependencyItem }) {
  return (
    <div className="text-xs bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 shadow-sm">
      <span className="font-mono">{edge.call_count}</span> calls
      {edge.avg_duration_ms !== null && (
        <span className="ml-1 text-gray-500">({edge.avg_duration_ms.toFixed(0)} ms)</span>
      )}
      {edge.error_count > 0 && (
        <span className="ml-1 text-red-600">{edge.error_count} errors</span>
      )}
    </div>
  );
}

export default function Topology() {
  const { data: graph, isLoading } = useTopology();

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading topology...</div>;

  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];

  // Simple layout: arrange nodes in rows
  const nodePositions = new Map<string, { x: number; y: number }>();
  const cols = Math.max(Math.ceil(Math.sqrt(nodes.length)), 1);
  nodes.forEach((node, i) => {
    nodePositions.set(node.service_name, {
      x: (i % cols) * 280 + 40,
      y: Math.floor(i / cols) * 180 + 40,
    });
  });

  const svgWidth = cols * 280 + 80;
  const svgHeight = (Math.ceil(nodes.length / cols)) * 180 + 80;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Service Topology</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Service dependency flowmap derived from trace data</p>
      </div>

      {nodes.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center text-gray-500 dark:text-gray-400">
          No services discovered yet. Send traces with multi-service spans to build the topology.
        </div>
      ) : (
        <>
          {/* Graph visualization */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 overflow-auto">
            <svg width={svgWidth} height={svgHeight} className="mx-auto">
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
                </marker>
              </defs>
              {/* Edges */}
              {edges.map(edge => {
                const from = nodePositions.get(edge.source_service);
                const to = nodePositions.get(edge.target_service);
                if (!from || !to) return null;
                return (
                  <g key={`${edge.source_service}-${edge.target_service}`}>
                    <line
                      x1={from.x + 100} y1={from.y + 50}
                      x2={to.x + 100} y2={to.y + 50}
                      stroke={edge.error_count > 0 ? '#ef4444' : '#94a3b8'}
                      strokeWidth={Math.min(Math.max(edge.call_count / 10, 1), 4)}
                      markerEnd="url(#arrowhead)"
                    />
                    <text
                      x={(from.x + to.x) / 2 + 100}
                      y={(from.y + to.y) / 2 + 45}
                      textAnchor="middle"
                      className="text-xs fill-gray-500 dark:fill-gray-400"
                      fontSize="11"
                    >
                      {edge.call_count} calls{edge.avg_duration_ms !== null ? ` (${edge.avg_duration_ms.toFixed(0)}ms)` : ''}
                    </text>
                  </g>
                );
              })}
            </svg>
            {/* Node cards overlaid */}
            <div className="flex flex-wrap gap-6 mt-4">
              {nodes.map(node => (
                <ServiceCard key={node.service_name} node={node} />
              ))}
            </div>
          </div>

          {/* Edge table */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Service Dependencies</h2>
            </div>
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Source</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">→</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Target</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Calls</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Errors</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Avg Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {edges.map(e => (
                  <tr key={e.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-6 py-3 text-sm font-medium text-gray-900 dark:text-white">{e.source_service}</td>
                    <td className="px-6 py-3 text-center text-gray-400">→</td>
                    <td className="px-6 py-3 text-sm font-medium text-gray-900 dark:text-white">{e.target_service}</td>
                    <td className="px-6 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{e.call_count}</td>
                    <td className="px-6 py-3 text-sm text-right">
                      <span className={e.error_count > 0 ? 'text-red-600 font-semibold' : 'text-gray-500'}>{e.error_count}</span>
                    </td>
                    <td className="px-6 py-3 text-sm text-right text-gray-700 dark:text-gray-300">
                      {e.avg_duration_ms !== null ? `${e.avg_duration_ms.toFixed(1)} ms` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
