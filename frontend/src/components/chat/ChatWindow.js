import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';
import { useChatContext } from '../../context/ChatContext';
import MessageBubble from './MessageBubble';

const ChatWindowContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;

const EmptyState = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #999;
  text-align: center;
  padding: 2rem;
`;

const EmptyTitle = styled.h3`
  margin-bottom: 1rem;
  font-size: 1.2rem;
`;

const EmptyText = styled.p`
  font-size: 0.9rem;
  max-width: 400px;
  line-height: 1.5;
`;

const ChatWindow = () => {
  const { messages, isLoading, currentThreadId } = useChatContext();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <ChatWindowContainer>
      {messages.length > 0 ? (
        <>
          {messages.map((message, index) => (
            <MessageBubble key={`${currentThreadId}-${index}`} message={message} />
          ))}
          {isLoading && (
            <MessageBubble 
              message={{
                text: "Thinking...",
                sender: "bot",
                userId: "SQL-Bot",
                timestamp: new Date().toISOString()
              }}
            />
          )}
          <div ref={bottomRef} />
        </>
      ) : (
        <EmptyState>
          <EmptyTitle>New Conversation</EmptyTitle>
          <EmptyText>
            Ask me anything about SQL queries, database design, or specific SQL commands.
          </EmptyText>
        </EmptyState>
      )}
    </ChatWindowContainer>
  );
};

export default ChatWindow;
