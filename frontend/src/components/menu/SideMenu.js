import React from 'react';
import styled from 'styled-components';
import { useChatContext } from '../../context/ChatContext';
import ChatHistory from './ChatHistory';

const MenuContainer = styled.div`
  width: 240px;
  background-color: #2c3e50;
  color: white;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 70px);
  overflow-y: auto;
`;

const MenuHeader = styled.div`
  font-size: 1.2rem;
  font-weight: bold;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #3d5166;
`;

const MenuItem = styled.button`
  padding: 0.8rem 1rem;
  margin-bottom: 0.5rem;
  background-color: ${props => props.active ? '#1e88e5' : 'transparent'};
  color: white;
  border: none;
  border-radius: 4px;
  text-align: left;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  transition: background-color 0.2s;

  &:hover {
    background-color: ${props => props.active ? '#1976d2' : '#3d5166'};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    &:hover {
      background-color: transparent;
    }
  }
`;

const MenuIcon = styled.span`
  margin-right: 0.5rem;
  font-size: 1.2rem;
`;

const MenuSection = styled.div`
  margin-bottom: 1.5rem;
`;

const SectionTitle = styled.div`
  font-size: 0.8rem;
  color: #a0aec0;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const NewThreadButton = styled.button`
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  padding: 0;
  transition: color 0.2s;
  
  &:hover {
    color: white;
  }
`;

const SideMenu = ({ currentUserId }) => {
  const { createNewThread } = useChatContext();
  // Check if user is admin
  const isAdmin = currentUserId === 'Admin';
  
  // Handle new thread creation
  const handleNewThread = () => {
    createNewThread();
  };

  return (
    <MenuContainer>
      <MenuHeader>SQL Matic</MenuHeader>

      <MenuSection>
        <SectionTitle>
          Conversations
          <NewThreadButton onClick={handleNewThread} title="New Thread">
            <MenuIcon>+</MenuIcon>
          </NewThreadButton>
        </SectionTitle>
        <ChatHistory />
      </MenuSection>

      <MenuSection>
        <SectionTitle>Tools</SectionTitle>
        <MenuItem disabled={!isAdmin}>
          <MenuIcon>⚙️</MenuIcon> Config
        </MenuItem>
        <MenuItem disabled={!isAdmin}>
          <MenuIcon>⬆️</MenuIcon> Upload
        </MenuItem>
        <MenuItem disabled={!isAdmin}>
          <MenuIcon>✓</MenuIcon> Evaluator
        </MenuItem>
      </MenuSection>
    </MenuContainer>
  );
};

export default SideMenu;
