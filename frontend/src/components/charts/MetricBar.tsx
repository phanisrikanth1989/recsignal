interface MetricBarProps {
  value: number | null;
  label?: string;
}

function getColor(value: number): string {
  if (value >= 95) return 'bg-red-500';
  if (value >= 85) return 'bg-yellow-500';
  return 'bg-green-500';
}

export default function MetricBar({ value, label }: MetricBarProps) {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 dark:text-gray-500 text-sm">-</span>;
  }

  return (
    <div className="flex items-center space-x-2 min-w-[120px]">
      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${getColor(value)}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className="text-xs text-gray-600 dark:text-gray-400 w-12 text-right">
        {value.toFixed(1)}%
      </span>
    </div>
  );
}
