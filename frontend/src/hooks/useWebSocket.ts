import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

type MessageHandler = (topic: string, data: unknown) => void;

const WS_RECONNECT_BASE_DELAY = 1000;
const WS_RECONNECT_MAX_DELAY = 30000;
const WS_PING_INTERVAL = 25000;

function getWsUrl(topics: string[]): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws?topics=${topics.join(',')}`;
}

/**
 * Hook that maintains a WebSocket connection and auto-invalidates React Query
 * caches when the server pushes updates.
 *
 * @param topics - Topics to subscribe to: "dashboard", "hosts", "host:{id}", "alerts"
 * @param onMessage - Optional callback for custom handling of incoming messages
 */
export function useWebSocket(topics: string[], onMessage?: MessageHandler) {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const pingTimer = useRef<ReturnType<typeof setInterval>>();
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getWsUrl(topics));
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectAttempt.current = 0;
      setConnected(true);
      // Keep-alive ping
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, WS_PING_INTERVAL);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const { topic, data } = msg;

        // Invalidate relevant React Query caches so UI updates instantly
        if (topic === 'dashboard') {
          queryClient.setQueryData(['dashboard-summary'], data);
        } else if (topic === 'hosts') {
          // Update the specific host in the hosts list cache
          queryClient.setQueryData<unknown[]>(['hosts'], (old) => {
            if (!old) return old;
            const hostData = data as { id: number };
            const idx = old.findIndex((h: any) => h.id === hostData.id);
            if (idx >= 0) {
              const updated = [...old];
              updated[idx] = { ...updated[idx] as object, ...data };
              return updated;
            }
            return [...old, data];
          });
        } else if (topic.startsWith('host:')) {
          const hostId = parseInt(topic.split(':')[1], 10);
          // Merge latest metrics into host-detail cache
          queryClient.setQueryData(['host-detail', hostId], (old: any) => {
            if (!old) return old;
            return { ...old, ...data };
          });
        } else if (topic === 'alerts') {
          // Invalidate to trigger refetch for alerts
          queryClient.invalidateQueries({ queryKey: ['alerts'] });
          queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
        }

        onMessage?.(topic, data);
      } catch {
        // Non-JSON message (e.g., pong) — ignore
      }
    };

    ws.onclose = () => {
      setConnected(false);
      clearInterval(pingTimer.current);
      // Reconnect with exponential backoff
      const delay = Math.min(
        WS_RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempt.current),
        WS_RECONNECT_MAX_DELAY,
      );
      reconnectAttempt.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [topics.join(','), queryClient, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      clearInterval(pingTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnect on intentional close
        wsRef.current.close();
        setConnected(false);
      }
    };
  }, [connect]);

  // Allow dynamic subscription from components
  const subscribe = useCallback((newTopics: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(`subscribe:${newTopics.join(',')}`);
    }
  }, []);

  const unsubscribe = useCallback((oldTopics: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(`unsubscribe:${oldTopics.join(',')}`);
    }
  }, []);

  return { subscribe, unsubscribe, connected };
}
