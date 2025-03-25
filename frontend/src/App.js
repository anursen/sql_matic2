import React from 'react';
import ChatUI from './components/ChatUI';
import LoginScreen from './components/LoginScreen';
import Header from './components/Header';
import { UserProvider, useUser } from './contexts/UserContext';
import './App.css';

// Main app content that renders based on authentication status
const AppContent = () => {
  const { user } = useUser();

  if (!user) {
    return <LoginScreen />;
  }

  return (
    <>
      <Header />
      <div className="app-content">
        <ChatUI />
      </div>
    </>
  );
};

function App() {
  return (
    <UserProvider>
      <div className="App">
        <AppContent />
      </div>
    </UserProvider>
  );
}

export default App;
