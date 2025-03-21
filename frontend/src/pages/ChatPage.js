import React from 'react';
import styled from 'styled-components';
import ChatWindow from '../components/chat/ChatWindow';
import ChatInput from '../components/chat/ChatInput';
import SideMenu from '../components/menu/SideMenu';
import DatabaseStructure from '../components/database/DatabaseStructure';
import { useChatContext } from '../context/ChatContext';

const ChatPageContainer = styled.div`
  display: flex;
  flex: 1;
  width: 100%;
`;

const MainContent = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  max-width: calc(100% - 520px); /* Adjust for both left and right sidebars */
  padding: 1rem;
  
  @media (max-width: 1200px) {
    max-width: calc(100% - 240px); /* Hide right sidebar on smaller screens */
  }
`;

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  height: calc(100vh - 120px);
  overflow: hidden;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
`;

const ChatPage = ({ currentUserId }) => {
  const { sendMessage } = useChatContext();

  const handleSendMessage = (text) => {
    sendMessage(text, currentUserId);
  };

  return (
    <ChatPageContainer>
      <SideMenu currentUserId={currentUserId} />
      <MainContent>
        <ChatContainer>
          <ChatWindow />
          <ChatInput onSendMessage={handleSendMessage} currentUserId={currentUserId} />
        </ChatContainer>
      </MainContent>
      <DatabaseStructure />
    </ChatPageContainer>
  );
};

export default ChatPage;
