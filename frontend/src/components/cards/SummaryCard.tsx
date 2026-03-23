import { Link } from 'react-router-dom';

interface SummaryCardProps {
  title: string;
  value: number;
  color?: string;
  to?: string;
}

const colorMap: Record<string, string> = {
  blue: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800',
  green: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800',
  yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-300 dark:border-yellow-800',
  red: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800',
  gray: 'bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700',
  orange: 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800',
};

export default function SummaryCard({ title, value, color = 'blue', to }: SummaryCardProps) {
  const classes = colorMap[color] || colorMap.blue;
  const content = (
    <div className={`rounded-lg border p-5 ${classes} ${to ? 'cursor-pointer hover:shadow-md hover:scale-[1.02] transition-all' : ''}`}>
      <p className="text-sm font-medium opacity-80">{title}</p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
    </div>
  );

  if (to) {
    return <Link to={to}>{content}</Link>;
  }
  return content;
}
