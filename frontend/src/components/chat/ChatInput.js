import React, { useState } from 'react';
import styled from 'styled-components';

const InputContainer = styled.div`
  display: flex;
  padding: 1rem;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
`;

const TextInput = styled.input`
  flex: 1;
  padding: 0.8rem 1rem;
  border: 1px solid #ced4da;
  border-radius: 20px;
  font-size: 1rem;
  outline: none;
  &:focus {
    border-color: #4dabf7;
  }
`;

const SendButton = styled.button`
  margin-left: 0.5rem;
  padding: 0.8rem 1.5rem;
  background-color: #1e88e5;
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #1976d2;
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const ChatInput = ({ onSendMessage, currentUserId }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message, currentUserId);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <InputContainer>
        <TextInput
          type="text"
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <SendButton type="submit" disabled={!message.trim()}>
          Send
        </SendButton>
      </InputContainer>
    </form>
  );
};

export default ChatInput;
