// filepath: market-research-platform/frontend/src/services/websocket.js
// SSE client for streaming chat responses from the FastAPI backend.

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Opens an SSE connection to the chat stream endpoint.
 * @param {number|null} sessionId - Current chat session ID
 * @param {string} question - User's question text
 * @param {function} onToken - Called with each streamed token string
 * @param {function} onSources - Called with final sources array when stream ends
 * @param {function} onSession - Called with session info { session_id }
 * @param {function} onError - Called if the stream errors
 * @param {function} onDone - Called when stream completes
 * @returns {EventSource} - The EventSource instance (call .close() to stop)
 */
export function openChatStream(sessionId, question, { onToken, onSources, onSession, onError, onDone }) {
  const params = new URLSearchParams({ q: question });
  if (sessionId) {
    params.set('session_id', sessionId);
  }

  const url = `${API_URL}/api/chat/stream?${params.toString()}`;
  const source = new EventSource(url);

  source.addEventListener('token', (e) => {
    // Unescape newlines that were escaped for SSE transport
    const token = e.data.replace(/\\n/g, '\n');
    onToken?.(token);
  });

  source.addEventListener('sources', (e) => {
    try {
      const sources = JSON.parse(e.data);
      onSources?.(sources);
    } catch (err) {
      console.error('Failed to parse sources:', err);
      onSources?.([]);
    }
  });

  source.addEventListener('session', (e) => {
    try {
      const data = JSON.parse(e.data);
      onSession?.(data);
    } catch (err) {
      console.error('Failed to parse session info:', err);
    }
  });

  source.addEventListener('error', (e) => {
    try {
      const data = JSON.parse(e.data);
      onError?.(new Error(data.error || 'Stream error'));
    } catch {
      // Generic SSE error event (not our custom error)
    }
  });

  source.addEventListener('done', (e) => {
    source.close();
    onDone?.();
  });

  source.onerror = (e) => {
    // EventSource auto-reconnects on error, but we want to stop
    if (source.readyState === EventSource.CLOSED) {
      onDone?.();
    } else {
      // Close the connection on error to prevent infinite reconnects
      source.close();
      onError?.(new Error('Connection lost'));
      onDone?.();
    }
  };

  return source;
}
