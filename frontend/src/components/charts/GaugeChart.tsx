import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

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

export default function GaugeChart({ value, label, size = 120 }: GaugeChartProps) {
  const v = value ?? 0;
  const color = getColor(v);
  const data = [
    { value: v },
    { value: 100 - v },
  ];

  return (
    <div className="flex flex-col items-center">
      <div style={{ width: size, height: size / 2 + 10 }} className="relative">
        <ResponsiveContainer width="100%" height={size}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={size * 0.3}
              outerRadius={size * 0.45}
              paddingAngle={0}
              dataKey="value"
              isAnimationActive={true}
              animationDuration={600}
            >
              <Cell fill={color} />
              <Cell fill="#e5e7eb" className="dark:fill-gray-700" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-x-0 bottom-0 text-center">
          <span className="text-lg font-bold" style={{ color }}>
            {value != null ? `${value.toFixed(1)}%` : '-'}
          </span>
        </div>
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">{label}</p>
    </div>
  );
}
