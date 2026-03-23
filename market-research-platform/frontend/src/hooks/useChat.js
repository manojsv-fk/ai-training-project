// filepath: market-research-platform/frontend/src/hooks/useChat.js
// Custom React hook managing chat state and streaming communication via SSE.

import { useState, useRef, useCallback } from 'react';
import { openChatStream } from '../services/websocket';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const sourceRef = useRef(null);

  const sendMessage = useCallback((text) => {
    if (!text.trim() || isLoading) return;

    // Append user message immediately (optimistic)
    const userMsg = {
      role: 'user',
      content: text,
      sources: [],
      timestamp: new Date().toISOString(),
    };

    // Create a placeholder assistant message that we'll stream into
    const assistantMsg = {
      role: 'assistant',
      content: '',
      sources: [],
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);

    // Open SSE stream
    sourceRef.current = openChatStream(sessionId, text, {
      onToken: (token) => {
        // Append token to the last (assistant) message
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            updated[updated.length - 1] = {
              ...lastMsg,
              content: lastMsg.content + token,
            };
          }
          return updated;
        });
      },

      onSources: (sources) => {
        // Attach sources to the last assistant message
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            updated[updated.length - 1] = {
              ...lastMsg,
              sources,
            };
          }
          return updated;
        });
      },

      onSession: (data) => {
        if (data.session_id) {
          setSessionId(data.session_id);
        }
      },

      onError: (error) => {
        console.error('Chat stream error:', error);
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.content) {
            updated[updated.length - 1] = {
              ...lastMsg,
              content: 'Sorry, I encountered an error. Please try again.',
              isStreaming: false,
            };
          }
          return updated;
        });
      },

      onDone: () => {
        // Mark streaming as complete
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            updated[updated.length - 1] = {
              ...lastMsg,
              isStreaming: false,
            };
          }
          return updated;
        });
        setIsLoading(false);
        sourceRef.current = null;
      },
    });
  }, [isLoading, sessionId]);

  const stopStreaming = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
      setIsLoading(false);
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
          updated[updated.length - 1] = { ...lastMsg, isStreaming: false };
        }
        return updated;
      });
    }
  }, []);

  const clearHistory = useCallback(() => {
    // Close any active stream
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
    setMessages([]);
    setSessionId(null);
    setIsLoading(false);
  }, []);

  return {
    messages,
    sendMessage,
    isLoading,
    clearHistory,
    stopStreaming,
    sessionId,
  };
}
