import React, { useState, useRef, useEffect } from 'react';
import { useUser } from '../contexts/UserContext';
import '../styles/Header.css';

const Header = () => {
  const { user, logout } = useUser();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownRef]);
  
  const toggleDropdown = () => {
    setDropdownOpen(!dropdownOpen);
  };
  
  return (
    <header className="app-header">
      <div className="header-logo">
        <h1>SQL Matic</h1>
      </div>
      
      {user && (
        <div className="profile-container" ref={dropdownRef}>
          <div className="profile-trigger" onClick={toggleDropdown}>
            <span className="username">{user.name}</span>
            <img
              src={user.avatar}
              alt={user.name}
              className="avatar"
            />
          </div>
          
          {dropdownOpen && (
            <div className="profile-dropdown">
              <div className="dropdown-header">
                <img src={user.avatar} alt={user.name} className="dropdown-avatar" />
                <div className="user-info">
                  <span className="dropdown-name">{user.name}</span>
                  <span className="dropdown-role">{user.role === 'admin' ? 'Administrator' : 'Regular User'}</span>
                </div>
              </div>
              
              <div className="dropdown-divider"></div>
              
              <ul className="dropdown-menu">
                <li onClick={() => alert('Account settings will be implemented soon')}>
                  <i className="dropdown-icon">⚙️</i> Account Settings
                </li>
                <li onClick={logout} className="logout-option">
                  <i className="dropdown-icon">🚪</i> Sign Out
                </li>
              </ul>
            </div>
          )}
        </div>
      )}
    </header>
  );
};

export default Header;
