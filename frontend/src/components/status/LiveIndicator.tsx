import { useState, useEffect, useRef } from 'react';

interface LiveIndicatorProps {
  connected: boolean;
}

export default function LiveIndicator({ connected }: LiveIndicatorProps) {
  return (
    <div className="flex items-center gap-1.5" title={connected ? 'Live — WebSocket connected' : 'Disconnected — using polling'}>
      <span className="relative flex h-2.5 w-2.5">
        {connected && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
        )}
        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
      </span>
      <span className={`text-xs font-medium ${connected ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>
        {connected ? 'Live' : 'Offline'}
      </span>
    </div>
  );
}
