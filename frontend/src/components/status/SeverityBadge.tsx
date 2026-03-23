const severityConfig: Record<string, { bg: string; text: string }> = {
  critical: { bg: 'bg-red-100', text: 'text-red-800' },
  warning: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
};

export default function SeverityBadge({ severity }: { severity: string }) {
  const cfg = severityConfig[severity] || { bg: 'bg-gray-100', text: 'text-gray-800' };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      {severity}
    </span>
  );
}
