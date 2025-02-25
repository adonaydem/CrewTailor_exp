import React, { createContext, useState } from 'react';

export const ThreadIdContext = createContext();

export const ThreadIdProvider = ({ children }) => {
  const [threadId, setThreadId] = useState(null);
  return (
    <ThreadIdContext.Provider value={{ threadId, setThreadId }}>
      {children}
    </ThreadIdContext.Provider>
  );
};