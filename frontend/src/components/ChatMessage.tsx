import React from 'react';
import { format } from 'date-fns';
import { ChatMessage as ChatMessageType } from '../types/api.ts';
import { Clock, Zap } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.type === 'user';
  const timestamp = new Date(message.timestamp);

  return (
    <div className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
      <div className="flex flex-col space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-medium text-sm">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <div className="flex items-center space-x-2 text-xs opacity-70">
            <Clock className="w-3 h-3" />
            <span>{format(timestamp, 'HH:mm')}</span>
            {message.processing_time_ms && (
              <>
                <Zap className="w-3 h-3" />
                <span>{message.processing_time_ms}ms</span>
              </>
            )}
          </div>
        </div>
        
        <div className="whitespace-pre-wrap break-words">
          {message.content}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 