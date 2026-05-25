/**
 * useSocket — creates a singleton Socket.IO connection and exposes
 * a stable emit function plus the raw socket for event listeners.
 */
import { useEffect, useRef } from 'react';
import { io } from 'socket.io-client';

const BACKEND_URL = 'http://localhost:8000';

let _socket = null;

function getSocket() {
  if (!_socket) {
    _socket = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
    });
  }
  return _socket;
}

export function useSocket() {
  const socketRef = useRef(getSocket());

  useEffect(() => {
    return () => {
      // Don't disconnect on unmount — we want the connection to persist
      // across screen transitions in this SPA.
    };
  }, []);

  return socketRef.current;
}
