interface GaugeChartProps {
  value: number | null | undefined;
  label: string;
  size?: number;
}

function getColor(value: number): string {
  if (value >= 95) return '#ef4444';
  if (value >= 85) return '#eab308';
  return '#22c55e';
}

export default function GaugeChart({ value, label, size = 140 }: GaugeChartProps) {
  const v = value ?? 0;
  const color = getColor(v);

  const cx = size / 2;
  const cy = size / 2;
  const strokeWidth = size * 0.12;
  const radius = (size - strokeWidth) / 2 - 2;

  // Semi-circle arc from 180° to 0° (left to right)
  const circumference = Math.PI * radius;
  const filledLength = (v / 100) * circumference;
  const emptyLength = circumference - filledLength;

  return (
    <div className="flex flex-col items-center" style={{ width: size }}>
      <svg
        width={size}
        height={size / 2 + 12}
        viewBox={`0 0 ${size} ${size / 2 + 12}`}
      >
        {/* Background arc (gray) */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Filled arc (colored) */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${filledLength} ${emptyLength}`}
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
        {/* Percentage text */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          dominantBaseline="auto"
          fill={color}
          fontSize={size * 0.16}
          fontWeight="bold"
        >
          {value != null ? `${value.toFixed(1)}%` : '-'}
        </text>
      </svg>
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mt-1 text-center">{label}</p>
    </div>
  );
}
