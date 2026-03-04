import { useEffect, useRef } from 'react';
import { useFilesStore } from '@/stores/files-store';
import type { FileProcessingEvent } from '@/types/api';

export function useSSE() {
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const baseDelay = 1000;

  const updateFileStatus = useFilesStore((state) => state.updateFileStatus);

  const connect = () => {
    if (eventSourceRef.current) {
      return;
    }

    const eventSource = new EventSource('/api/v0/events/stream', {
      withCredentials: true,
    });

    eventSource.onopen = () => {
      console.log('[SSE] Connected');
      reconnectAttempts.current = 0;
    };

    eventSource.addEventListener('FileProcessingEvent', (event) => {
      try {
        console.log('[SSE] File processing message arrived!');
        const data: FileProcessingEvent = JSON.parse(event.data);
        
        // Update file status in store
        updateFileStatus(data.file_id, data.status, data.progress);
    
        console.log('[SSE] File processing update:', data);
      } catch (error) {
        console.error('[SSE] Error parsing event data:', error);
      }
    });

    eventSource.onmessage = (event) => {
      console.log('[SSE] Default message event:', event);
    };

    eventSource.onerror = () => {
      console.error('[SSE] Connection error');
      eventSource.close();
      eventSourceRef.current = null;

      // Implement exponential backoff reconnection
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = baseDelay * Math.pow(2, reconnectAttempts.current);
        console.log(`[SSE] Reconnecting in ${delay}ms...`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, delay);
      } else {
        console.error('[SSE] Max reconnection attempts reached');
      }
    };

    eventSourceRef.current = eventSource;
  };

  const disconnect = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    reconnectAttempts.current = 0;
  };

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, []);

  return { connect, disconnect };
}