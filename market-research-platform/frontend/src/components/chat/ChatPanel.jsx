// filepath: market-research-platform/frontend/src/components/chat/ChatPanel.jsx
// Right-side chat panel with message thread, input, and collapsing support.

import React, { useState, useRef, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Trash2, MessageSquare } from 'lucide-react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { useChat } from '../../hooks/useChat';

const EXAMPLE_QUESTIONS = [
  "What are the top supply chain risks mentioned across our reports?",
  "Summarize the key AI adoption trends in logistics.",
  "What recommendations do the reports make for Q2 strategy?",
];

function ChatPanel() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const messagesEndRef = useRef(null);
  const { messages, sendMessage, isLoading, clearHistory, stopStreaming } = useChat();

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (text) => {
    sendMessage(text);
  };

  const handleSuggestionClick = (question) => {
    sendMessage(question);
  };

  return (
    <aside className={`chat-panel ${isCollapsed ? 'chat-panel--collapsed' : ''}`}>
      <div className="chat-panel__header">
        {!isCollapsed && (
          <>
            <h2>
              <MessageSquare size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
              Research Q&A
            </h2>
            {messages.length > 0 && (
              <button
                className="btn btn--sm btn--secondary"
                onClick={clearHistory}
                title="Clear chat"
              >
                <Trash2 size={12} />
              </button>
            )}
          </>
        )}
        <button
          className="chat-panel__toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label={isCollapsed ? 'Expand chat' : 'Collapse chat'}
        >
          {isCollapsed ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>

      {!isCollapsed && (
        <>
          <div className="chat-panel__messages">
            {messages.length === 0 && (
              <div className="chat-panel__empty">
                <MessageSquare size={32} style={{ marginBottom: 8, opacity: 0.3 }} />
                <p>Ask anything about your research corpus.</p>
                <div className="chat-panel__suggestions">
                  {EXAMPLE_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      className="chat-panel__suggestion"
                      onClick={() => handleSuggestionClick(q)}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg, idx) => (
              <ChatMessage key={idx} message={msg} />
            ))}
            {isLoading && messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && (
              <div style={{ paddingLeft: 8 }}>
                <span className="loading-spinner" />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            onStop={stopStreaming}
          />
        </>
      )}
    </aside>
  );
}

export default ChatPanel;
