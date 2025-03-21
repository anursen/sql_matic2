import React from 'react';
import styled from 'styled-components';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const MessageContainer = styled.div`
  display: flex;
  margin-bottom: 1rem;
  justify-content: ${props => props.isUser ? 'flex-end' : 'flex-start'};
`;

const BubbleWrapper = styled.div`
  max-width: 70%;
  display: flex;
  flex-direction: column;
`;

const Bubble = styled.div`
  padding: 0.8rem 1rem;
  border-radius: 18px;
  background-color: ${props => props.isUser ? '#1e88e5' : '#f1f0f0'};
  color: ${props => props.isUser ? 'white' : 'black'};
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  overflow: hidden;

  a {
    color: ${props => props.isUser ? '#e1f5fe' : '#0277bd'};
    text-decoration: underline;
  }

  pre {
    margin: 0;
  }

  p {
    margin: 0.5rem 0;
    &:first-child {
      margin-top: 0;
    }
    &:last-child {
      margin-bottom: 0;
    }
  }

  ul, ol {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
  }

  table {
    border-collapse: collapse;
    margin: 0.5rem 0;
    overflow-x: auto;
    display: block;
  }

  th, td {
    border: 1px solid ${props => props.isUser ? '#90caf9' : '#bbdefb'};
    padding: 0.4rem 0.6rem;
    text-align: left;
  }

  th {
    background-color: ${props => props.isUser ? '#2196f3' : '#e3f2fd'};
  }

  code:not([class*="language-"]) {
    background-color: ${props => props.isUser ? '#0d47a1' : '#e0e0e0'};
    border-radius: 3px;
    padding: 0.2rem 0.4rem;
    font-family: 'Courier New', Courier, monospace;
  }

  img {
    max-width: 100%;
    border-radius: 8px;
  }
`;

const Timestamp = styled.div`
  font-size: 0.7rem;
  color: #999;
  margin-top: 0.3rem;
  text-align: ${props => props.isUser ? 'right' : 'left'};
  display: flex;
  justify-content: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  align-items: center;
  gap: 5px;
`;

const UserId = styled.span`
  font-weight: bold;
  color: ${props => props.isUser ? '#1e88e5' : '#666'};
`;

const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const MessageBubble = ({ message }) => {
  const { text, sender, timestamp, userId } = message;
  const isUser = sender === 'user';
  const displayName = userId || (isUser ? 'User' : 'SQL-Matic');

  return (
    <MessageContainer isUser={isUser}>
      <BubbleWrapper>
        <Bubble isUser={isUser}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={{
              code({node, inline, className, children, ...props}) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={atomDark}
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
              }
            }}
          >
            {text}
          </ReactMarkdown>
        </Bubble>
        <Timestamp isUser={isUser}>
          {formatTime(timestamp)}
          <UserId isUser={isUser}>{displayName}</UserId>
        </Timestamp>
      </BubbleWrapper>
    </MessageContainer>
  );
};

export default MessageBubble;
