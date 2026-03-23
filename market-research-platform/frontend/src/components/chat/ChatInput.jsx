// filepath: market-research-platform/frontend/src/components/chat/ChatInput.jsx
// Text input bar at the bottom of the chat panel.

import React, { useState } from 'react';
import { Send, Square } from 'lucide-react';

function ChatInput({ onSend, isLoading, onStop }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSend(text.trim());
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <textarea
        className="chat-input__field"
        placeholder="Ask a question about your research..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
        rows={2}
      />
      {isLoading ? (
        <button
          type="button"
          className="chat-input__send"
          onClick={onStop}
          aria-label="Stop streaming"
          title="Stop"
        >
          <Square size={14} />
        </button>
      ) : (
        <button
          type="submit"
          className="chat-input__send"
          disabled={!text.trim()}
          aria-label="Send message"
        >
          <Send size={14} />
        </button>
      )}
    </form>
  );
}

export default ChatInput;
