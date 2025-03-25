import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { useUser } from '../contexts/UserContext';
import Metrics from './Metrics';
import '../styles/ChatUI.css';

const ChatUI = () => {
  const { user } = useUser();
  const [socket, setSocket] = useState(null);
  const [threadId, setThreadId] = useState('');
  const [userId, setUserId] = useState('');
  const [agentId, setAgentId] = useState('');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('Not connected');
  const [statusColor, setStatusColor] = useState('black');
  const [currentMessageId, setCurrentMessageId] = useState(null);
  // Add state for metrics
  const [metrics, setMetrics] = useState(null);

  // Use refs to track displayed messages and tool calls
  const displayedMessagesRef = useRef(new Set());
  const displayedToolCallsRef = useRef(new Set());
  const messagesEndRef = useRef(null);

  // Set user ID from logged in user
  useEffect(() => {
    if (user) {
      setUserId(user.id);
    }
  }, [user]);

  useEffect(() => {
    // Scroll to bottom whenever messages change
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const connectWebSocket = () => {
    // Close existing connection if any
    if (socket) {
      socket.close();
    }

    // Get thread ID from input or generate a random one
    let threadIdToUse = threadId;
    if (!threadIdToUse) {
      threadIdToUse = 'thread-' + Math.random().toString(36).substring(2, 9);
      setThreadId(threadIdToUse);
    }

    // Connect to WebSocket
    const clientId = 'client-' + Math.random().toString(36).substring(2, 9);
    const newSocket = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
    setSocket(newSocket);

    newSocket.onopen = () => {
      setConnectionStatus('Connected');
      setStatusColor('green');
      addMessage('system', `Connected to thread: ${threadIdToUse}`);
      
      // Clear message tracking on new connection
      displayedMessagesRef.current.clear();
      displayedToolCallsRef.current.clear();
      
      // Reset metrics
      resetMetrics();
    };

    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data);

      if (data.type === 'chat_message') {
        const message = data.payload.message;
        
        // Create a message identifier based on role and content
        const messageId = `${message.role}:${message.content}`;
        
        // Only display if we haven't already shown this message
        if (!displayedMessagesRef.current.has(messageId)) {
          if (message.role === 'user') {
            // Skip - we already added the user message on the client side
            // Just mark it as displayed
            displayedMessagesRef.current.add(messageId);
          }
        }
      } else if (data.type === 'token_stream') {
        const { token, message_id, is_complete } = data.payload;
        
        if (is_complete) {
          // Mark streaming as complete - we're done with this message
          completeStreamingMessage(message_id);
        } else {
          // Update the streaming message with the new token
          updateStreamingMessage(token, message_id);
        }
      } else if (data.type === 'typing_indicator') {
        if (data.payload.isTyping) {
          // Prevent duplicate typing indicators
          if (!messages.some(msg => msg.id === 'typing-indicator')) {
            addMessage('system', 'Assistant is typing...', 'typing-indicator');
          }
        } else {
          removeElement('typing-indicator');
        }
      } else if (data.type === 'error') {
        addMessage('error', data.payload.message);
      } else if (data.type === 'tool_calls') {
        // Create a unique ID for the tool call based on content
        const toolCallId = JSON.stringify(data.payload.tool_calls);
        
        // Only display if we haven't shown this tool call before
        if (!displayedToolCallsRef.current.has(toolCallId)) {
          addMessage('system', `Using tool: ${JSON.stringify(data.payload.tool_calls)}`);
          displayedToolCallsRef.current.add(toolCallId);
        }
      } else if (data.type === 'metrics') {
        // Update metrics display with received data
        updateMetricsDisplay(data.payload);
      }
    };

    newSocket.onclose = (event) => {
      if (event.wasClean) {
        setConnectionStatus('Disconnected');
        setStatusColor('black');
      } else {
        setConnectionStatus('Connection lost');
        setStatusColor('red');
      }
    };

    newSocket.onerror = (error) => {
      setConnectionStatus('Error: ' + error.message);
      setStatusColor('red');
    };
  };

  const disconnectWebSocket = () => {
    if (socket) {
      socket.close();
      setConnectionStatus('Disconnected');
      setStatusColor('black');
    }
  };

  const updateStreamingMessage = (token, messageId) => {
    // If this is a new message ID or we don't have a current streaming message
    if (messageId !== currentMessageId || !messages.some(msg => msg.id === 'streaming-' + messageId)) {
      setCurrentMessageId(messageId);
      
      // Create a new streaming message element
      setMessages(prev => [
        ...prev, 
        {
          role: 'assistant',
          content: token,
          id: 'streaming-' + messageId
        }
      ]);
    } else {
      // Append to existing streaming message
      setMessages(prev => prev.map(msg => {
        if (msg.id === 'streaming-' + messageId) {
          return { ...msg, content: msg.content + token };
        }
        return msg;
      }));
    }
  };

  const completeStreamingMessage = (messageId) => {
    // Just mark as complete - the message is already in the UI from streaming
    setCurrentMessageId(null);
  };

  const addMessage = (role, content, id = null) => {
    // Create a message identifier
    const messageId = `${role}:${content}`;
    
    // Skip if we've already displayed this message
    if (displayedMessagesRef.current.has(messageId) && role !== 'system') {
      return;
    }
    
    // Mark as displayed
    displayedMessagesRef.current.add(messageId);
    
    setMessages(prev => [
      ...prev,
      {
        role,
        content,
        id: id || messageId
      }
    ]);
  };

  const removeElement = (id) => {
    setMessages(prev => prev.filter(msg => msg.id !== id));
  };

  // Add function to reset metrics
  const resetMetrics = () => {
    setMetrics({
      tokenUsage: { prompt: 0, completion: 0, total: 0 },
      performance: { totalTime: 0, llmTime: 0 },
      toolUsage: { totalCalls: 0, lastUsed: null }
    });
  };

  // Add function to update metrics
  const updateMetricsDisplay = (metricsData) => {
    console.log('Updating metrics:', metricsData);
    if (!metricsData) return;
    
    setMetrics(metricsData);
  };

  const sendMessage = () => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      alert('Please connect to a WebSocket first');
      return;
    }
    
    const trimmedMessage = message.trim();
    if (!trimmedMessage) {
      alert('Please enter a message');
      return;
    }
    
    // Reset message tracking for new conversation turn
    displayedToolCallsRef.current.clear();
    
    // Reset metrics when sending new message
    resetMetrics();
    
    // Add user message to UI and track it
    const messageId = `user:${trimmedMessage}`;
    if (!displayedMessagesRef.current.has(messageId)) {
      addMessage('user', trimmedMessage);
      // The addMessage function will add it to displayedMessages
    }
    
    // Prepare proper payload based on the structure expected by the server
    const payload = {
      message: trimmedMessage,
      thread_id: threadId,
      user_id: userId
    };
    
    // Add optional agent_id if provided
    if (agentId) {
      payload.agent_id = agentId;
    }
    
    // Send message through WebSocket
    socket.send(JSON.stringify({
      type: 'chat_message',
      payload: payload
    }));
    
    // Clear input
    setMessage('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className="app-container">
      <div className="chat-container">
        <div className="chat-header">
          <h1>SQL Matic Chat</h1>
        </div>
        
        <div className="connection-controls">
          <div className="input-group">
            <label htmlFor="thread-id">Thread ID</label>
            <input 
              type="text" 
              id="thread-id" 
              value={threadId} 
              onChange={(e) => setThreadId(e.target.value)} 
              placeholder="Leave empty for new thread" 
            />
          </div>
          
          <div className="input-group">
            <label htmlFor="user-id">User ID</label>
            <input 
              type="text" 
              id="user-id" 
              value={userId} 
              onChange={(e) => setUserId(e.target.value)} 
              readOnly
              title="This is set from your login"
              className="readonly-input"
            />
          </div>
          
          <div className="input-group">
            <label htmlFor="agent-id">Agent ID (Optional)</label>
            <input 
              type="text" 
              id="agent-id" 
              value={agentId} 
              onChange={(e) => setAgentId(e.target.value)} 
              placeholder="Optional agent ID" 
            />
          </div>
          
          <div className="button-group">
            <button onClick={connectWebSocket}>Connect</button>
            <button onClick={disconnectWebSocket}>Disconnect</button>
          </div>
        </div>
        
        <div className="connection-status" style={{ color: statusColor }}>
          {connectionStatus}
        </div>
        
        <div className="chat-body">
          <h2>Conversation</h2>
          <div className="messages-container">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                {msg.role === 'system' || msg.role === 'error' ? (
                  <>
                    <strong>
                      {msg.role === 'system' ? 'System' : 'Error'}:
                    </strong>{' '}
                    <span className="markdown-content">
                      {msg.content}
                    </span>
                  </>
                ) : (
                  <ReactMarkdown
                    className="markdown-content"
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                    components={{
                      code({node, inline, className, children, ...props}) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <SyntaxHighlighter
                            style={tomorrow}
                            language={match[1]}
                            PreTag="div"
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      },
                      table({node, ...props}) {
                        return (
                          <div className="table-container">
                            <table {...props} />
                          </div>
                        );
                      }
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          
          <div className="message-input-container">
            <input 
              type="text" 
              id="message" 
              value={message} 
              onChange={(e) => setMessage(e.target.value)} 
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..." 
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      </div>
      
      {/* Add the Metrics component */}
      <Metrics metrics={metrics} resetMetrics={resetMetrics} />
    </div>
  );
};

export default ChatUI;
