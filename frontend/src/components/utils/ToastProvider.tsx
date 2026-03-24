import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';

interface Toast {
  id: number;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  hostname?: string;
  metric?: string;
}

interface ToastContextType {
  addToast: (toast: Omit<Toast, 'id'>) => void;
}

const ToastContext = createContext<ToastContextType>({ addToast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

const TOAST_DURATION = 6000;
const MAX_TOASTS = 5;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(0);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = nextId.current++;
    setToasts((prev) => [...prev.slice(-(MAX_TOASTS - 1)), { ...toast, id }]);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={() => removeToast(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

const severityStyles: Record<string, string> = {
  critical: 'border-red-500 bg-red-50 dark:bg-red-900/40 text-red-800 dark:text-red-200',
  warning: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200',
  info: 'border-blue-500 bg-blue-50 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200',
};

const severityIcons: Record<string, string> = {
  critical: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z',
  warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z',
  info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
};

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setExiting(true), TOAST_DURATION - 300);
    const removeTimer = setTimeout(onDismiss, TOAST_DURATION);
    return () => {
      clearTimeout(timer);
      clearTimeout(removeTimer);
    };
  }, [onDismiss]);

  return (
    <div
      className={`pointer-events-auto flex items-start gap-3 p-3 rounded-lg border-l-4 shadow-lg backdrop-blur-sm max-w-sm transition-all duration-300 ${
        severityStyles[toast.severity] || severityStyles.info
      } ${exiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'}`}
    >
      <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d={severityIcons[toast.severity] || severityIcons.info} />
      </svg>
      <div className="flex-1 min-w-0">
        {toast.hostname && (
          <p className="text-xs font-semibold opacity-70 mb-0.5">{toast.hostname}</p>
        )}
        <p className="text-sm font-medium truncate">{toast.message}</p>
        {toast.metric && (
          <p className="text-xs opacity-60 mt-0.5">{toast.metric}</p>
        )}
      </div>
      <button
        onClick={onDismiss}
        className="shrink-0 opacity-50 hover:opacity-100 text-lg leading-none"
      >
        &times;
      </button>
    </div>
  );
}
