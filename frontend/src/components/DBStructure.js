import React, { useState, useEffect } from 'react';
import { FaTable, FaKey, FaLink, FaChevronDown, FaChevronRight, FaDatabase, FaExclamationTriangle, FaSync } from 'react-icons/fa';
import axios from 'axios';
import './DBStructure.css';

const DBStructure = () => {
  const [schema, setSchema] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTables, setExpandedTables] = useState({});

  // Fetch schema data from API
  useEffect(() => {
    const fetchSchema = async () => {
      setLoading(true);
      try {
        console.log('Fetching schema from /api/database/schema');
        const response = await axios.get('/api/database/schema');
        console.log('Schema response:', response.data);
        
        if (response.data && response.data.tables) {
          setSchema(response.data.tables);
          
          // Initialize expanded state for tables (all collapsed by default)
          const expanded = {};
          response.data.tables.forEach(table => {
            expanded[table.table_name] = false;
          });
          setExpandedTables(expanded);
        } else {
          setError('Invalid schema data received: ' + JSON.stringify(response.data));
        }
      } catch (err) {
        console.error('Error fetching database schema:', err);
        const errorMessage = err.response 
          ? `Error ${err.response.status}: ${err.response.data?.error || err.response.statusText}` 
          : `Error: ${err.message}`;
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchSchema();
  }, []);

  // Toggle table expansion
  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }));
  };

  // Refresh schema data
  const refreshSchema = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Refreshing schema from /api/database/schema');
      const response = await axios.get('/api/database/schema');
      console.log('Schema refresh response:', response.data);
      
      if (response.data && response.data.tables) {
        setSchema(response.data.tables);
      } else {
        setError('Invalid schema data received: ' + JSON.stringify(response.data));
      }
    } catch (err) {
      console.error('Error refreshing database schema:', err);
      const errorMessage = err.response 
        ? `Error ${err.response.status}: ${err.response.data?.error || err.response.statusText}` 
        : `Error: ${err.message}`;
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Render loading state
  if (loading && schema.length === 0) {
    return (
      <div className="db-structure-container">
        <div className="db-structure-header">
          <h3><FaDatabase /> Database Structure</h3>
        </div>
        <div className="db-structure-loading">
          <div className="loading-spinner"></div>
          <p>Loading database structure...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error && schema.length === 0) {
    return (
      <div className="db-structure-container">
        <div className="db-structure-header">
          <h3><FaDatabase /> Database Structure</h3>
          <button className="refresh-button" onClick={refreshSchema} title="Refresh schema">
            <FaSync />
          </button>
        </div>
        <div className="db-structure-error">
          <FaExclamationTriangle />
          <p>{error}</p>
          <button onClick={refreshSchema}>Try Again</button>
        </div>
      </div>
    );
  }

  return (
    <div className="db-structure-container">
      <div className="db-structure-header">
        <h3><FaDatabase /> Database Structure</h3>
        <button className="refresh-button" onClick={refreshSchema} title="Refresh schema">
          <FaSync />
        </button>
      </div>
      
      {loading && (
        <div className="refresh-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}
      
      <div className="db-structure-content">
        {schema.length === 0 ? (
          <div className="empty-state">
            <p>No tables found in the database.</p>
          </div>
        ) : (
          <ul className="table-list">
            {schema.map((table) => (
              <li key={table.table_name} className="table-item">
                <div 
                  className="table-header" 
                  onClick={() => toggleTable(table.table_name)}
                >
                  <div className="table-name">
                    {expandedTables[table.table_name] ? <FaChevronDown /> : <FaChevronRight />}
                    <FaTable className="table-icon" />
                    {table.table_name}
                    <span className="column-count">{table.columns.length} columns</span>
                  </div>
                </div>
                
                {expandedTables[table.table_name] && (
                  <div className="table-details">
                    <ul className="column-list">
                      {table.columns.map((column) => (
                        <li key={`${table.table_name}-${column.name}`} className="column-item">
                          <div className="column-info">
                            <span className="column-name">
                              {column.is_primary_key && <FaKey className="primary-key-icon" title="Primary Key" />}
                              {column.is_foreign_key && <FaLink className="foreign-key-icon" title="Foreign Key" />}
                              {column.name}
                            </span>
                            <span className="column-type">{column.type}</span>
                          </div>
                          {column.is_foreign_key && column.references && (
                            <div className="reference-info">
                              →&nbsp;{column.references.referenced_table}.{column.references.referenced_column}
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default DBStructure;
