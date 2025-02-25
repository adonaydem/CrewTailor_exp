import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { useAuth, AuthProvider } from './contexts/AuthContext';
import { UIStateProvider, useUIState } from './contexts/UIStateContext';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MainContent from './components/MainContent2';
import WorkflowView from './components/WorkflowView';
import WorkflowRun from './components/WorkflowRun';
import NewWorkflows from './components/NewWorkflows';
import Store from './components/Store';
import Challenge from './components/Challenge';
import ConsoleFooter from './components/ConsoleFooter';
import Onboarding from './components/Onboarding';
import './App.css';
import 'react-flow-renderer/dist/style.css';
import 'react-flow-renderer/dist/theme-default.css';
import '@fortawesome/fontawesome-free/css/all.min.css';

function App() {
  const { currentUser } = useAuth();
  const {
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

  } = useUIState();

  return (
    <Router>
      <div className="app">
        {currentUser && (
          <Header
            toggleSidebar={toggleSidebar}
            isSidebarCollapsed={isSidebarCollapsed}
            toggleConsole={toggleConsole}
            isConsoleCollapsed={isConsoleCollapsed}
          />
        )}
        <div className="main-container custom-scrollbar">
          {currentUser && <Sidebar isCollapsed={isSidebarCollapsed} currentWorkflow={currentWorkflow} onThreadSelect={setSelectedThreadId} onThreadSelectPAM={setSelectedThreadIdPAM} setIsConsoleCollapsed={setIsConsoleCollapsed}/>}
          <div className={`content-container ${isSidebarCollapsed ? 'expanded' : ''}`}>
            <Routes>
              <Route path="/onboarding" element={<Onboarding />} />
              <Route
                path="/"
                element={currentUser ? <MainContent setCurrentWorkflow={setCurrentWorkflow} /> : <Navigate to="/onboarding" />}
              />
              <Route path="/newWorkflows" element={<NewWorkflows setCurrentWorkflow={setCurrentWorkflow}/>} />
              <Route
                path="/workflowView"
                element={<WorkflowView currentWorkflow={currentWorkflow} setCurrentWorkflow={setCurrentWorkflow} />}
              />
              <Route
                path="/workflowRun"
                element={<WorkflowRun currentWorkflow={currentWorkflow} setCurrentWorkflow={setCurrentWorkflow} setIsConsoleCollapsed={setIsConsoleCollapsed} selectedThreadId={selectedThreadId} selectedChallenge={selectedChallenge} />}
              />
              <Route
                path="/store"
                element={<Store setCurrentWorkflow={setCurrentWorkflow} />}
              />
              <Route
                path="/challenge"
                element={<Challenge setCurrentWorkflow={setCurrentWorkflow} selectedChallenge={selectedChallenge} setSelectedChallenge={setSelectedChallenge}/>}
              />
            </Routes>
            {!isConsoleCollapsed && currentUser && (
              <ConsoleFooter setIsConsoleCollapsed={setIsConsoleCollapsed} isSidebarCollapsed={isSidebarCollapsed} selectedThreadIdPAM={selectedThreadIdPAM}/>
            )}
          </div>
        </div>
      </div>
    </Router>
  );
}

export default function WrappedApp() {
  return (
    <AuthProvider>
      <UIStateProvider>
        <App />
      </UIStateProvider>
    </AuthProvider>
  );
}