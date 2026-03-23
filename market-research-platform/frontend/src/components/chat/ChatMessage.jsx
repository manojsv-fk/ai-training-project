// filepath: market-research-platform/frontend/src/components/chat/ChatMessage.jsx
// Renders a single chat message bubble with markdown support and source citations.

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';

function ChatMessage({ message }) {
  const { role, content, sources = [], timestamp, isStreaming } = message;
  const [showSources, setShowSources] = useState(false);

  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className={`chat-message chat-message--${role}`}>
      <div className="chat-message__bubble">
        {role === 'assistant' ? (
          <>
            <ReactMarkdown>{content}</ReactMarkdown>
            {isStreaming && <span className="chat-message__streaming-cursor" />}
          </>
        ) : (
          <p>{content}</p>
        )}
      </div>

      {/* Source citations (assistant only) */}
      {role === 'assistant' && sources.length > 0 && (
        <div className="chat-message__sources">
          <button
            className="chat-message__sources-toggle"
            onClick={() => setShowSources(!showSources)}
          >
            <FileText size={10} style={{ marginRight: 3, verticalAlign: -1 }} />
            {sources.length} source{sources.length !== 1 ? 's' : ''}
            {showSources ? <ChevronUp size={10} style={{ marginLeft: 2 }} /> : <ChevronDown size={10} style={{ marginLeft: 2 }} />}
          </button>
          {showSources && (
            <ul className="chat-message__sources-list">
              {sources.map((src, idx) => (
                <li key={idx} className="chat-message__source-item">
                  <span>{src.source_name}</span>
                  {src.page && <span> &middot; p.{src.page}</span>}
                  {src.score && <span> &middot; {(src.score * 100).toFixed(0)}%</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <span className="chat-message__timestamp">{formattedTime}</span>
    </div>
  );
}

export default ChatMessage;
