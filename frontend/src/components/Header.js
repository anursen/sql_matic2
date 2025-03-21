import React, { useState } from 'react';
import styled from 'styled-components';
import LoginModal from './auth/LoginModal';

const HeaderContainer = styled.header`
  background-color: #2c3e50;
  color: white;
  padding: 0.8rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 70px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const Logo = styled.h1`
  margin: 0;
  font-size: 1.5rem;
`;

const LoginButton = styled.button`
  background-color: transparent;
  color: white;
  border: 1px solid white;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;

  &:hover {
    background-color: white;
    color: #2c3e50;
  }
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const UserProfile = styled.div`
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
`;

const Avatar = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: ${props => props.isAdmin ? '#e74c3c' : '#3498db'};
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.5rem;
  font-weight: bold;
`;

const UserName = styled.span`
  font-size: 0.9rem;
`;

const UserDropdown = styled.div`
  position: relative;
`;

const DropdownMenu = styled.div`
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 150px;
  z-index: 100;
  overflow: hidden;
`;

const DropdownItem = styled.button`
  padding: 0.8rem 1rem;
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  color: #333;
  transition: background-color 0.2s;
  font-size: 0.9rem;
  
  &:hover {
    background-color: #f5f5f5;
  }
`;

const Header = ({ currentUser, onLogin, onLogout }) => {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  
  const isAdmin = currentUser === 'Admin';
  const userInitial = currentUser ? currentUser.charAt(0) : '';

  const handleLoginClick = () => {
    setShowLoginModal(true);
  };

  const handleLoginSubmit = (userId) => {
    setShowLoginModal(false);
    onLogin(userId);
  };

  const handleLogout = () => {
    setShowDropdown(false);
    onLogout();
  };

  const toggleDropdown = () => {
    setShowDropdown(!showDropdown);
  };

  return (
    <HeaderContainer>
      <Logo>SQL Matic Chat</Logo>
      <UserInfo>
        {currentUser ? (
          <UserDropdown>
            <UserProfile onClick={toggleDropdown}>
              <Avatar isAdmin={isAdmin}>{userInitial}</Avatar>
              <UserName>{currentUser}</UserName>
            </UserProfile>
            {showDropdown && (
              <DropdownMenu>
                <DropdownItem onClick={handleLogout}>Logout</DropdownItem>
              </DropdownMenu>
            )}
          </UserDropdown>
        ) : (
          <LoginButton onClick={handleLoginClick}>Login</LoginButton>
        )}
      </UserInfo>

      {showLoginModal && (
        <LoginModal 
          onClose={() => setShowLoginModal(false)} 
          onLogin={handleLoginSubmit}
        />
      )}
    </HeaderContainer>
  );
};

export default Header;
