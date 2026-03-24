interface MetricBarProps {
  value: number | null;
  label?: string;
}

function getColor(value: number): string {
  if (value >= 95) return 'bg-red-500';
  if (value >= 85) return 'bg-yellow-500';
  return 'bg-green-500';
}

function getTextColor(value: number): string {
  if (value >= 95) return 'text-red-600 dark:text-red-400';
  if (value >= 85) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-gray-600 dark:text-gray-400';
}

export default function MetricBar({ value, label }: MetricBarProps) {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 dark:text-gray-500 text-sm">-</span>;
  }

  return (
    <div className="flex items-center space-x-2 min-w-[120px]">
      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ease-in-out ${getColor(value)}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className={`text-xs w-12 text-right font-medium transition-colors duration-500 ${getTextColor(value)}`}>
        {value.toFixed(1)}%
      </span>
    </div>
  );
}
