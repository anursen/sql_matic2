import React, { createContext, useContext, useState } from 'react';

const DatabaseContext = createContext();

// Initial metrics state
const initialMetrics = {
  tokenUsage: {
    prompt: 0,
    completion: 0,
    total: 0
  },
  databaseStats: {
    databaseCount: 0,
    tableCount: 0,
    rowCount: 0
  },
  performance: {
    averageResponseTime: 0,
    lastQueryTime: 0
  },
  lastUpdated: new Date().toISOString()
};

export const DatabaseProvider = ({ children }) => {
  const [databaseStructure, setDatabaseStructure] = useState({
    databases: []
  });
  
  const [metrics, setMetrics] = useState(initialMetrics);

  // Function to update the database structure
  const updateDatabaseStructure = (newStructure) => {
    setDatabaseStructure(newStructure);
    
    // Update database stats in metrics
    if (newStructure && newStructure.databases) {
      const tableCount = newStructure.databases.reduce(
        (count, db) => count + (db.tables ? db.tables.length : 0), 
        0
      );
      
      setMetrics(prevMetrics => ({
        ...prevMetrics,
        databaseStats: {
          ...prevMetrics.databaseStats,
          databaseCount: newStructure.databases.length,
          tableCount
        },
        lastUpdated: new Date().toISOString()
      }));
    }
  };
  
  // Function to update metrics
  const updateMetrics = (newMetrics) => {
    setMetrics({
      ...metrics,
      ...newMetrics,
      lastUpdated: new Date().toISOString()
    });
  };
  
  // Function to update token usage
  const updateTokenUsage = (prompt, completion) => {
    const total = prompt + completion;
    setMetrics(prevMetrics => ({
      ...prevMetrics,
      tokenUsage: {
        prompt,
        completion,
        total
      },
      lastUpdated: new Date().toISOString()
    }));
  };
  
  // Function to update performance metrics
  const updatePerformance = (responseTime) => {
    setMetrics(prevMetrics => {
      const currentAvg = prevMetrics.performance.averageResponseTime;
      // Simple running average calculation
      const newAvg = currentAvg === 0 
        ? responseTime 
        : (currentAvg * 0.7) + (responseTime * 0.3); // weighted average
        
      return {
        ...prevMetrics,
        performance: {
          averageResponseTime: Math.round(newAvg),
          lastQueryTime: responseTime
        },
        lastUpdated: new Date().toISOString()
      };
    });
  };

  return (
    <DatabaseContext.Provider
      value={{
        databaseStructure,
        updateDatabaseStructure,
        metrics,
        updateMetrics,
        updateTokenUsage,
        updatePerformance
      }}
    >
      {children}
    </DatabaseContext.Provider>
  );
};

export const useDatabaseContext = () => {
  const context = useContext(DatabaseContext);
  if (!context) {
    throw new Error('useDatabaseContext must be used within a DatabaseProvider');
  }
  return context;
};
