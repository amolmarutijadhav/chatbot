import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="chat-message assistant">
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600">Assistant is typing</span>
        <div className="typing-indicator">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator; 