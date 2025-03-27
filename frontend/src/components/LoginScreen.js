import React, { useState } from 'react';
import { useUser } from '../contexts/UserContext';
import '../styles/components/login.css';

const LoginScreen = () => {
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('user');
  const { login } = useUser();
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!username.trim()) {
      alert('Please enter a username');
      return;
    }
    
    // Login with user information
    login({
      id: `user-${Date.now()}`,
      name: username,
      role: role,
      avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(username)}&background=random`
    });
  };
  
  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>SQL Matic</h1>
          <p>Please sign in to continue</p>
        </div>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="role">Account Type</label>
            <div className="role-selector">
              <button
                type="button"
                className={role === 'user' ? 'active' : ''}
                onClick={() => setRole('user')}
              >
                Regular User
              </button>
              <button
                type="button"
                className={role === 'admin' ? 'active' : ''}
                onClick={() => setRole('admin')}
              >
                Admin
              </button>
            </div>
          </div>
          
          <button type="submit" className="login-button">
            Sign In
          </button>
          
          <div className="login-footer">
            <p>
              <small>
                Note: This is a demo app. Later, this will be replaced with Google OAuth.
              </small>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginScreen;
