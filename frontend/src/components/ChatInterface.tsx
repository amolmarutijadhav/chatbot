import React, { useState, useEffect, useRef } from 'react';
import { Bot, RefreshCw, Settings } from 'lucide-react';
import ChatMessage from './ChatMessage.tsx';
import ChatInput from './ChatInput.tsx';
import TypingIndicator from './TypingIndicator.tsx';
import SystemStatus from './SystemStatus.tsx';
import { ChatMessage as ChatMessageType } from '../types/api.ts';
import { chatAPI, systemAPI } from '../services/api.ts';

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize session and load system status
  useEffect(() => {
    const initializeChat = async () => {
      try {
        setLoading(true);
        
        // Create a new session
        const session = await chatAPI.createSession({
          user_id: 'frontend-user',
          metadata: { source: 'web-frontend' }
        });
        setCurrentSession(session.session_id);

        // Load system status
        const [healthData, statsData] = await Promise.all([
          systemAPI.getHealth(),
          systemAPI.getStats()
        ]);
        
        setHealth(healthData);
        setStats(statsData);

        // Add welcome message
        setMessages([{
          id: 'welcome',
          content: `Hello! I'm your Intelligent MCP Chatbot. I'm here to help you with any questions or tasks. The system is currently ${healthData.status} with ${healthData.components?.api_server?.endpoints || 0} endpoints available.`,
          timestamp: new Date().toISOString(),
          type: 'assistant',
          session_id: session.session_id
        }]);

      } catch (err: any) {
        console.error('Failed to initialize chat:', err);
        
        // Check if it's a server connection issue
        if (err.code === 'ERR_NETWORK' || err.response?.status >= 500) {
          setError('Failed to connect to the chatbot. Please check if the server is running.');
        } else {
          setError('Failed to initialize chat. Please refresh the page and try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    initializeChat();
  }, []);

  const handleSendMessage = async (content: string) => {
    if (!currentSession || isTyping) return;

    // Add user message
    const userMessage: ChatMessageType = {
      id: `user-${Date.now()}`,
      content,
      timestamp: new Date().toISOString(),
      type: 'user',
      session_id: currentSession
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      // Send message to API
      const response = await chatAPI.sendMessage({
        message: content,
        session_id: currentSession,
        message_type: 'chat'
      });

      // Add assistant response
      const assistantMessage: ChatMessageType = {
        id: response.message_id,
        content: response.content,
        timestamp: response.timestamp,
        type: 'assistant',
        session_id: response.session_id,
        processing_time_ms: response.processing_time_ms
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Refresh stats
      const newStats = await systemAPI.getStats();
      setStats(newStats);

    } catch (err: any) {
      console.error('Failed to send message:', err);
      
      // Check if it's a session not found error
      if (err.response?.status === 500 && err.response?.data?.error?.includes('Session') && err.response?.data?.error?.includes('not found')) {
        // Session expired, create a new one and retry
        try {
          console.log('Session expired, creating new session...');
          const newSession = await chatAPI.createSession({
            user_id: 'frontend-user',
            metadata: { source: 'web-frontend' }
          });
          setCurrentSession(newSession.session_id);
          
          // Retry the message with new session
          const retryResponse = await chatAPI.sendMessage({
            message: content,
            session_id: newSession.session_id,
            message_type: 'chat'
          });
          
          // Add assistant response
          const assistantMessage: ChatMessageType = {
            id: retryResponse.message_id,
            content: retryResponse.content,
            timestamp: retryResponse.timestamp,
            type: 'assistant',
            session_id: retryResponse.session_id,
            processing_time_ms: retryResponse.processing_time_ms
          };
          
          setMessages(prev => [...prev, assistantMessage]);
          
          // Refresh stats
          const newStats = await systemAPI.getStats();
          setStats(newStats);
          
        } catch (retryErr) {
          console.error('Failed to create new session and retry:', retryErr);
          setError('Session expired and failed to create new session. Please refresh the page.');
        }
      } else {
        setError('Failed to send message. Please try again.');
      }
    } finally {
      setIsTyping(false);
    }
  };

  const handleNewSession = async () => {
    try {
      setMessages([]);
      setIsTyping(true);

      const session = await chatAPI.createSession({
        user_id: 'frontend-user',
        metadata: { source: 'web-frontend' }
      });
      
      setCurrentSession(session.session_id);
      
      setMessages([{
        id: 'welcome',
        content: 'New session started! How can I help you today?',
        timestamp: new Date().toISOString(),
        type: 'assistant',
        session_id: session.session_id
      }]);

    } catch (err) {
      console.error('Failed to create new session:', err);
      setError('Failed to create new session. Please try again.');
    } finally {
      setIsTyping(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to chatbot...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Bot className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">MCP Chatbot</h1>
              <p className="text-sm text-gray-500">Intelligent Assistant</p>
            </div>
          </div>
        </div>

        <div className="flex-1 p-4 space-y-4 overflow-y-auto">
          <SystemStatus health={health} stats={stats} loading={false} />
          
          <div className="space-y-2">
            <button
              onClick={handleNewSession}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>New Session</span>
            </button>
            
            <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors">
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Chat</h2>
              <p className="text-sm text-gray-500">
                Session: {currentSession?.slice(0, 8)}...
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm text-gray-500">
                {health?.status || 'Unknown'}
              </span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {isTyping && <TypingIndicator />}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isTyping || !currentSession}
          placeholder={isTyping ? "Assistant is typing..." : "Type your message..."}
        />
      </div>
    </div>
  );
};

export default ChatInterface; 