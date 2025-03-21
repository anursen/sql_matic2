import React, { useState } from 'react';
import styled from 'styled-components';
import Metrics from './Metrics';

const StructureContainer = styled.div`
  width: 280px;
  background-color: white;
  border-left: 1px solid #e9ecef;
  height: calc(100vh - 70px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
`;

const Header = styled.div`
  padding: 1rem;
  font-weight: bold;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Title = styled.h3`
  margin: 0;
  font-size: 1rem;
  color: #333;
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 2rem;
  color: #999;
  text-align: center;
`;

const EmptyIcon = styled.div`
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #ccc;
`;

const EmptyText = styled.p`
  margin: 0;
  font-size: 0.9rem;
`;

const DatabaseList = styled.div`
  padding: 0.5rem;
`;

const Database = styled.div`
  margin-bottom: 1rem;
`;

const DatabaseName = styled.div`
  font-weight: bold;
  padding: 0.5rem;
  cursor: pointer;
  background-color: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const TableList = styled.div`
  margin-left: 1rem;
  ${props => !props.isOpen && 'display: none;'}
`;

const Table = styled.div`
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  border-radius: 4px;
  
  &:hover {
    background-color: #f1f3f5;
  }
`;

const ColumnList = styled.div`
  margin-left: 1rem;
  font-size: 0.85rem;
  ${props => !props.isOpen && 'display: none;'}
`;

const Column = styled.div`
  padding: 0.3rem 0.5rem;
  display: flex;
  justify-content: space-between;
  
  &:hover {
    background-color: #f8f9fa;
    border-radius: 4px;
  }
`;

const ColumnName = styled.span`
  color: #333;
`;

const ColumnType = styled.span`
  color: #999;
  font-size: 0.8rem;
`;

const CollapseIcon = styled.span`
  transition: transform 0.2s;
  transform: ${props => props.isOpen ? 'rotate(90deg)' : 'rotate(0)'};
`;

// Mock data structure - to be replaced with actual data later
const mockDatabaseStructure = {
  databases: [
    {
      name: 'Sample Database',
      tables: [
        {
          name: 'users',
          columns: [
            { name: 'id', type: 'INT PRIMARY KEY' },
            { name: 'username', type: 'VARCHAR(50)' },
            { name: 'email', type: 'VARCHAR(100)' },
            { name: 'created_at', type: 'TIMESTAMP' }
          ]
        },
        {
          name: 'products',
          columns: [
            { name: 'id', type: 'INT PRIMARY KEY' },
            { name: 'name', type: 'VARCHAR(100)' },
            { name: 'price', type: 'DECIMAL(10,2)' },
            { name: 'category_id', type: 'INT' }
          ]
        }
      ]
    }
  ]
};

const DatabaseStructure = ({ dbStructure = null }) => {
  const [openDatabases, setOpenDatabases] = useState({});
  const [openTables, setOpenTables] = useState({});
  
  // Use provided dbStructure or fall back to mock data
  const structure = dbStructure || mockDatabaseStructure;
  
  const toggleDatabase = (dbName) => {
    setOpenDatabases({
      ...openDatabases,
      [dbName]: !openDatabases[dbName]
    });
  };
  
  const toggleTable = (tableName) => {
    setOpenTables({
      ...openTables,
      [tableName]: !openTables[tableName]
    });
  };

  return (
    <StructureContainer>
      <Header>
        <Title>Database Structure</Title>
      </Header>
      
      {structure.databases.length > 0 ? (
        <DatabaseList>
          {structure.databases.map(db => (
            <Database key={db.name}>
              <DatabaseName onClick={() => toggleDatabase(db.name)}>
                <span>{db.name}</span>
                <CollapseIcon isOpen={openDatabases[db.name]}>▶</CollapseIcon>
              </DatabaseName>
              
              <TableList isOpen={openDatabases[db.name]}>
                {db.tables.map(table => (
                  <div key={table.name}>
                    <Table onClick={() => toggleTable(table.name)}>
                      <span>{table.name}</span>
                    </Table>
                    
                    <ColumnList isOpen={openTables[table.name]}>
                      {table.columns.map(column => (
                        <Column key={column.name}>
                          <ColumnName>{column.name}</ColumnName>
                          <ColumnType>{column.type}</ColumnType>
                        </Column>
                      ))}
                    </ColumnList>
                  </div>
                ))}
              </TableList>
            </Database>
          ))}
        </DatabaseList>
      ) : (
        <EmptyState>
          <EmptyIcon>📊</EmptyIcon>
          <EmptyText>No database structure available yet.</EmptyText>
          <EmptyText>Database schema will appear here when loaded.</EmptyText>
        </EmptyState>
      )}

      {/* Add Metrics component at the bottom */}
      <Metrics />
    </StructureContainer>
  );
};

export default DatabaseStructure;
