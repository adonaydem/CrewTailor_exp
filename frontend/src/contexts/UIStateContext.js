import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

const UIStateContext = createContext();

export const UIStateProvider = ({ children }) => {
  const { currentUser } = useAuth();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    // Retrieve from localStorage or initialize as null
    return localStorage.getItem('isSidebarCollapsed') || true;
  });
  const [isConsoleCollapsed, setIsConsoleCollapsed] = useState(() => {
    // Retrieve from localStorage or initialize as null
    return localStorage.getItem('isConsoleCollapsed') || false;
  });
  const [currentWorkflow, setCurrentWorkflow] = useState(() => {
    // Retrieve from localStorage or initialize as null
    return localStorage.getItem('currentWorkflow') || null;
  });
  const [selectedThreadId, setSelectedThreadId] = useState(null);
  const [selectedThreadIdPAM, setSelectedThreadIdPAM] = useState(null);
  const [isChallenge, setIsChallenge] = useState(false);
  const [selectedChallenge, setSelectedChallenge] = useState(null);

  useEffect(() => {
    if (currentUser) {
      // Set default states when the user logs in
      setIsSidebarCollapsed(true);
      setIsConsoleCollapsed(false);
      setCurrentWorkflow(null);
      setSelectedThreadId(null);
      setSelectedThreadIdPAM(null); 
      setIsChallenge(false);
      setSelectedChallenge(null);
    } else {
      // Reset states when the user logs out
      setIsSidebarCollapsed(true);
      setIsConsoleCollapsed(false);
      setCurrentWorkflow(null);
      setSelectedThreadId(null);
      setSelectedThreadIdPAM(null);
      setIsChallenge(false);
      setSelectedChallenge(null);
    }
  }, [currentUser]);

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const toggleConsole = () => {
    setIsConsoleCollapsed(!isConsoleCollapsed);
  };

  return (
    <UIStateContext.Provider
      value={{
        isSidebarCollapsed,
        toggleSidebar,
        isConsoleCollapsed,
        toggleConsole,
        currentWorkflow,
        setCurrentWorkflow,
        setIsConsoleCollapsed,
        selectedThreadId,
        setSelectedThreadId,
        selectedThreadIdPAM,
        setSelectedThreadIdPAM,
        selectedChallenge,
        setSelectedChallenge
      }}
    >
      {children}
    </UIStateContext.Provider>
  );
};

export const useUIState = () => useContext(UIStateContext);
