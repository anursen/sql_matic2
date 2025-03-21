import React from 'react';
import styled from 'styled-components';

const MetricsContainer = styled.div`
  padding: 1rem;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
  margin-top: auto;
`;

const MetricsTitle = styled.h4`
  margin: 0 0 0.8rem 0;
  font-size: 0.9rem;
  color: #495057;
  display: flex;
  align-items: center;
`;

const MetricsIcon = styled.span`
  margin-right: 0.5rem;
  font-size: 1rem;
`;

const MetricsList = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.7rem;
`;

const MetricItem = styled.div`
  background-color: white;
  padding: 0.7rem;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
`;

const MetricLabel = styled.div`
  font-size: 0.7rem;
  color: #6c757d;
  margin-bottom: 0.3rem;
`;

const MetricValue = styled.div`
  font-size: 0.9rem;
  font-weight: 600;
  color: #343a40;
`;

const TimestampWrapper = styled.div`
  margin-top: 0.8rem;
  text-align: right;
  font-size: 0.7rem;
  color: #adb5bd;
`;

// Mock metrics data - to be replaced with actual data later
const mockMetrics = {
  tokenUsage: {
    prompt: 450,
    completion: 230,
    total: 680
  },
  databaseStats: {
    databaseCount: 1,
    tableCount: 12,
    rowCount: 5723
  },
  performance: {
    averageResponseTime: 245, // in ms
    lastQueryTime: 178 // in ms
  },
  lastUpdated: new Date().toISOString()
};

const formatNumber = (num) => {
  return num.toLocaleString();
};

const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { 
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });
};

const Metrics = ({ metrics = null }) => {
  // Use provided metrics or fall back to mock data
  const data = metrics || mockMetrics;
  
  return (
    <MetricsContainer>
      <MetricsTitle>
        <MetricsIcon>📊</MetricsIcon>
        Usage Metrics
      </MetricsTitle>
      
      <MetricsList>
        <MetricItem>
          <MetricLabel>Token Usage</MetricLabel>
          <MetricValue>{formatNumber(data.tokenUsage.total)} tokens</MetricValue>
        </MetricItem>
        
        <MetricItem>
          <MetricLabel>Tables</MetricLabel>
          <MetricValue>{formatNumber(data.databaseStats.tableCount)}</MetricValue>
        </MetricItem>
        
        <MetricItem>
          <MetricLabel>Row Count</MetricLabel>
          <MetricValue>{formatNumber(data.databaseStats.rowCount)}</MetricValue>
        </MetricItem>
        
        <MetricItem>
          <MetricLabel>Response Time</MetricLabel>
          <MetricValue>{data.performance.lastQueryTime} ms</MetricValue>
        </MetricItem>
      </MetricsList>
      
      <TimestampWrapper>
        Last updated: {formatTime(data.lastUpdated)}
      </TimestampWrapper>
    </MetricsContainer>
  );
};

export default Metrics;
