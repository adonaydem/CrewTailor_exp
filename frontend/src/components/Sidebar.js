import React, { useState, useEffect } from 'react';
import './Sidebar.css';
import { workflows } from './data';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import useSocketCrew from '../hooks/useSocketCrew';
import { format, parseISO, isToday, isYesterday, isThisWeek } from 'date-fns';

const Sidebar = ({ isCollapsed, currentWorkflow, onThreadSelect, onThreadSelectPAM, setIsConsoleCollapsed }) => {
  const [threads, setThreads] = useState([]);
  const [threadsPAM, setThreadsPAM] = useState([]);
  const location = useLocation();
  const { currentUser } = useAuth();
  const { emitAbort } = useSocketCrew(null, currentWorkflow);
  const BackendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (location.pathname.includes('workflowRun')) {
      fetchThreads();
      const intervalId = setInterval(fetchThreads, 5000); // fetch every 5 seconds

      return () => clearInterval(intervalId); // cleanup on unmount
    }else{
      fetchThreadsPAM();
      const intervalId = setInterval(fetchThreadsPAM, 5000); // fetch every 5 seconds

      return () => clearInterval(intervalId); // cleanup on unmount
    }
  }, [location]);

  const fetchThreads = async () => {
    try {
      const response = await fetch(
        `${BackendUrl}/threads/${currentUser.uid}?workflowId=${encodeURIComponent(currentWorkflow)}`,
        { method: 'GET' }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('!!!!!!API Response threads:', data);
      setThreads(data);
    } catch (err) {
      console.error('Error fetching threads:', err);
    }
  };
  
  const fetchThreadsPAM = async () => {
    try {
      const response = await fetch(
        `${BackendUrl}/threads/${currentUser.uid}`,
        { method: 'GET' }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response threads pam:', data);
      setThreadsPAM(data);
    } catch (err) {
      console.error('Error fetching threads:', err);
    }
  };

  const handleThreadSelect = (threadId) => {
    emitAbort();
    onThreadSelect(threadId);
  };
  const handleThreadSelectPAM = (threadId) => {
    onThreadSelectPAM(threadId);
    setIsConsoleCollapsed(false);
  };

  const truncateMessage = (message, wordLimit) => {
    const words = message.split(' ');
    return words.length > wordLimit ? words.slice(0, wordLimit).join(' ') + '...' : message;
  };

  const formatDate = (dateString) => {
    const date = parseISO(dateString);
    return format(date, 'MMM dd, yyyy hh:mm a');
  };

  const categorizeThreads = (threads) => {
    const Today = [];
    const Yesterday = [];
    const LastWeek = [];
    const Earlier = [];

    threads.forEach((thread) => {
      const date = parseISO(thread.timestamp);

      if (isToday(date)) {
        Today.push(thread);
      } else if (isYesterday(date)) {
        Yesterday.push(thread);
      } else if (isThisWeek(date)) {
        LastWeek.push(thread);
      } else {
        Earlier.push(thread);
      }
    });

    return { Today, Yesterday, LastWeek, Earlier };
  };

  const categorizedThreads = categorizeThreads(threads);
  const categorizedThreadsPAM = categorizeThreads(threadsPAM);
  return (
    <div className={`custom-scrollbar sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      
      {location.pathname.includes('workflowRun') && (
        <div className="threads-section">
          <div className="threads-header">
            <span>Instances</span>
          </div>
          <div className="threads-list">
            {Object.keys(categorizedThreads).map((category) =>
              categorizedThreads[category].length > 0 ? (
                <div key={category} className="thread-category">
                  <div className="thread-category-header">{category}</div>
                  {categorizedThreads[category].map((thread) => (
                    <div
                      className="thread-item"
                      onClick={() => handleThreadSelect(thread.thread_id)}
                    >
                      <span className="thread-timestamp">{formatDate(thread.timestamp)}</span>
                      <span className="thread-message">
                        {truncateMessage(thread.messages[thread.messages.length - 1].text, 10)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : null
            )}
          </div>
        </div>
      )}
      {!location.pathname.includes('workflowRun') && (
        <div className="threads-section">
          <div className="threads-header">
            <span>PAM chat history</span>
          </div>
          <div className="threads-list">
            {Object.keys(categorizedThreadsPAM).map((category) =>
              categorizedThreadsPAM[category].length > 0 ? (
                <div key={category} className="thread-category">
                  <div className="thread-category-header">{category}</div>
                  {categorizedThreadsPAM[category].map((thread) => (
                    <div
                      className="thread-item"
                      onClick={() => handleThreadSelectPAM(thread.thread_id)}
                    >
                      <span className="thread-timestamp">{formatDate(thread.timestamp)}</span>
                      <span className="thread-message">
                        {truncateMessage(thread.messages[thread.messages.length - 1].text, 10)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : null
            )}
          </div>
        </div>
      )}

      
    </div>
  );
};

export default Sidebar;