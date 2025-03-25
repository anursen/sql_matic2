import React from 'react';

const Metrics = ({ metrics, resetMetrics }) => {
  // Handle null or undefined metrics
  const tokenUsage = metrics?.tokenUsage || { prompt: 0, completion: 0, total: 0 };
  const performance = metrics?.performance || { totalTime: 0, llmTime: 0 };
  const toolUsage = metrics?.toolUsage || { totalCalls: 0, lastUsed: null };

  // Format tool arguments for display
  const formatToolArgs = (args) => {
    if (!args) return '';
    
    try {
      if (typeof args === 'string') {
        return args.length > 30 ? args.substring(0, 30) + '...' : args;
      } else {
        const argsStr = JSON.stringify(args);
        return argsStr.length > 30 ? argsStr.substring(0, 30) + '...' : argsStr;
      }
    } catch (e) {
      return '[complex args]';
    }
  };

  return (
    <div className="metrics-panel">
      <div className="metrics-header">
        <h2>Metrics</h2>
      </div>
      <div className="metrics-body">
        <div className="metrics-grid">
          <div className="metric-group">
            <div className="metric-label">Token Usage</div>
            <div className="metric-value">
              Prompt: {tokenUsage.prompt || 0} | Completion: {tokenUsage.completion || 0} | Total: {tokenUsage.total || 0}
            </div>
          </div>
          
          <div className="metric-group">
            <div className="metric-label">Performance</div>
            <div className="metric-value">
              Total: {Math.round(performance.totalTime || 0)}ms | LLM: {Math.round(performance.llmTime || 0)}ms
            </div>
          </div>
          
          <div className="metric-group">
            <div className="metric-label">Tool Calls</div>
            <div className="metric-value">
              Total Calls: {toolUsage.totalCalls || 0}
            </div>
          </div>
        </div>
        
        <div className="tool-usage">
          <div className="tool-title">Last Tool Used</div>
          <div className="tool-item">
            {toolUsage.lastUsed ? (
              <>
                <span className="tool-name">{toolUsage.lastUsed.name}</span>
                {formatToolArgs(toolUsage.lastUsed.args)}
              </>
            ) : (
              'None'
            )}
          </div>
        </div>
        
        <div style={{ marginTop: '1rem', textAlign: 'center' }}>
          <button 
            onClick={resetMetrics}
            style={{
              backgroundColor: 'var(--bg-secondary)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
              padding: '0.5rem 1rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.875rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            Reset Metrics
          </button>
        </div>
      </div>
    </div>
  );
};

export default Metrics;
