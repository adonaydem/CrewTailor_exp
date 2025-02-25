import React from 'react';
import './Header.css';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import logo from '../static/logo5.png';
const Header = ({ toggleSidebar, isSidebarCollapsed, toggleConsole, isConsoleCollapsed }) => {
  const { currentUser } = useAuth();
  const { logout } = useAuth();
  const navigate = useNavigate(); // Correctly call useNavigate here

  console.log(currentUser);

  const handleNewWorkflowsClick = () => {
    navigate('/newWorkflows');
  };

  const handleCrewTailorClick = () => {
    navigate('/');
  };
  const handleStoreClick = () => {
    navigate('/store');
  };
  const handleLogOut = async (e) => {
    e.preventDefault();
    try {
      await logout();
      navigate('/onboarding');
    } catch (error) {
      console.error('Failed to log out', error);
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <button className="toggle-button" onClick={toggleSidebar}>
          <i className={`fas ${isSidebarCollapsed ? 'fa-angle-double-right' : 'fa-angle-double-left'}`}></i>
        </button>
        
        <h1><a href="/" onClick={handleCrewTailorClick}>CrewTailor</a></h1>
      </div>
      <img src={logo} alt="CrewTailor Logo" className="header-logo" />
      <nav>
        {isConsoleCollapsed && (
          <button className="console-button" onClick={toggleConsole}>
            PAM Console
          </button>
        )}

        <div className="dropdown">
          <button className="dropbtn">Workflows ▼</button>
          <div className="dropdown-content">
            <span className="dropdown-element" onClick={handleNewWorkflowsClick} style={{ cursor: 'pointer' }}>New Workflow</span>
          </div>
        </div>
        <button className="console-button" onClick={handleStoreClick}>
            Store
          </button>
          <button className="console-button" onClick={() => navigate('/challenge')}>
            Doli's Challenge
          </button>
        {currentUser && (
          <button className="console-button" onClick={handleLogOut}>
            Logout
          </button>
        )}
      </nav>
    </header>
  );
};

export default Header;