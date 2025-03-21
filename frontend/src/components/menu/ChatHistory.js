import React from 'react';
import styled from 'styled-components';
import { useChatContext } from '../../context/ChatContext';

const HistoryContainer = styled.div`
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  max-height: 300px;
`;

const ThreadItem = styled.div`
  padding: 0.8rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  background-color: ${props => props.active ? '#1e88e5' : 'rgba(255, 255, 255, 0.1)'};
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: ${props => props.active ? '#1976d2' : 'rgba(255, 255, 255, 0.2)'};
  }
`;

const ThreadTitle = styled.div`
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ThreadTimestamp = styled.div`
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
`;

const EmptyState = styled.div`
  padding: 1rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  font-style: italic;
`;

const formatDate = (timestamp) => {
  if (!timestamp) return '';
  
  const date = new Date(timestamp);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  
  if (isToday) {
    return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  }
  
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const isYesterday = date.toDateString() === yesterday.toDateString();
  
  if (isYesterday) {
    return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  }
  
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + 
         ` at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
};

const ChatHistory = () => {
  const { threads, currentThreadId, switchThread } = useChatContext();
  
  // Handle thread selection
  const handleThreadSelect = (threadId) => {
    switchThread(threadId);
  };
  
  if (threads.length === 0) {
    return <EmptyState>No conversation history yet</EmptyState>;
  }
  
  return (
    <HistoryContainer>
      {threads.map(thread => (
        <ThreadItem 
          key={thread.id}
          active={thread.id === currentThreadId}
          onClick={() => handleThreadSelect(thread.id)}
        >
          <ThreadTitle>{thread.name}</ThreadTitle>
          <ThreadTimestamp>
            {formatDate(thread.lastMessageTime)}
          </ThreadTimestamp>
        </ThreadItem>
      ))}
    </HistoryContainer>
  );
};

export default ChatHistory;
