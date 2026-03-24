const UNITS: [string, number][] = [
  ['y', 31536000],
  ['mo', 2592000],
  ['d', 86400],
  ['h', 3600],
  ['m', 60],
  ['s', 1],
];

export function timeAgo(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 0) return 'just now';
  if (seconds < 5) return 'just now';
  for (const [unit, value] of UNITS) {
    const count = Math.floor(seconds / value);
    if (count >= 1) return `${count}${unit} ago`;
  }
  return 'just now';
}

import { useState, useEffect } from 'react';

interface TimeAgoProps {
  date: string | null | undefined;
  className?: string;
}

export function TimeAgo({ date, className = '' }: TimeAgoProps) {
  const [, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(id);
  }, []);

  const full = date ? new Date(date).toLocaleString() : '';

  return (
    <span className={className} title={full}>
      {timeAgo(date)}
    </span>
  );
}
