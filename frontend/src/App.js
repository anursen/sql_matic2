import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import styled from 'styled-components';
import ChatPage from './pages/ChatPage';
import Header from './components/Header';
import { ChatProvider } from './context/ChatContext';
import { DatabaseProvider } from './context/DatabaseContext';
import LoginModal from './components/auth/LoginModal';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
`;

const ContentContainer = styled.div`
  flex: 1;
  display: flex;
`;

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [showInitialLogin, setShowInitialLogin] = useState(true);

  // Check if user was previously logged in
  useEffect(() => {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      setCurrentUser(savedUser);
      setShowInitialLogin(false);
    }
  }, []);

  const handleLogin = (userId) => {
    setCurrentUser(userId);
    setShowInitialLogin(false);
    // Save to localStorage for persistent login
    localStorage.setItem('currentUser', userId);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    // Clear from localStorage
    localStorage.removeItem('currentUser');
  };

  return (
    <ChatProvider>
      <DatabaseProvider>
        <Router>
          <AppContainer>
            <Header 
              currentUser={currentUser} 
              onLogin={handleLogin} 
              onLogout={handleLogout} 
            />
            {currentUser ? (
              <ContentContainer>
                <Routes>
                  <Route path="/" element={<ChatPage currentUserId={currentUser} />} />
                </Routes>
              </ContentContainer>
            ) : (
              showInitialLogin && (
                <LoginModal 
                  onClose={() => setShowInitialLogin(false)} 
                  onLogin={handleLogin}
                />
              )
            )}
          </AppContainer>
        </Router>
      </DatabaseProvider>
    </ChatProvider>
  );
}

export default App;
