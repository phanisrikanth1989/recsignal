import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
}

export default function Sparkline({ data, color, height = 24 }: SparklineProps) {
  if (!data || data.length < 2) return null;

  const max = Math.max(...data);
  const lineColor = color || (max >= 95 ? '#ef4444' : max >= 85 ? '#eab308' : '#22c55e');

  const chartData = data.map((value, i) => ({ v: value }));

  return (
    <div style={{ width: 80, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <YAxis domain={[0, 100]} hide />
          <Line
            type="monotone"
            dataKey="v"
            stroke={lineColor}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
