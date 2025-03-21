from datetime import datetime
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Column(BaseModel):
    """Database column model"""
    name: str
    type: str
    primary_key: bool = False
    foreign_key: bool = False
    references: Optional[Dict[str, str]] = None

class Table(BaseModel):
    """Database table model"""
    name: str
    columns: List[Column] = []

class TableStats(BaseModel):
    """Statistics for a database table"""
    name: str
    row_count: int = 0
    column_count: int = 0
    index_count: int = 0
    estimated_size_bytes: int = 0

class Database(BaseModel):
    """Database model"""
    name: str
    tables: List[Table] = []

class DatabaseInfo(BaseModel):
    """Database file and configuration information"""
    name: str
    path: str
    size_bytes: int
    page_size: int = 0
    page_count: int = 0
    encoding: str = ""
    journal_mode: str = ""
    creation_time: Optional[str] = None
    modification_time: Optional[str] = None

class DatabaseStats(BaseModel):
    """Database statistics metrics"""
    databaseCount: int = 0
    tableCount: int = 0
    rowCount: int = 0

class DatabaseStructure(BaseModel):
    """Database structure model"""
    databases: List[Database] = []

class GetSqliteMetadata(BaseModel):
    """Input for SQLite metadata extraction tool"""
    db_path: str = Field(description="Path to the SQLite database file")

class SQLiteMetadataResponse(BaseModel):
    """Response model for SQLite metadata"""
    database_info: DatabaseInfo
    table_stats: List[TableStats] = []
    stats: DatabaseStats
    error: Optional[str] = None

class GetSqliteSchemaResponse(BaseModel):
    """Output for SQLite schema extraction tool"""
    database_schema: Dict[str, Any] = Field(..., description="The database schema information")
    tables: Optional[List[str]] = None
    error: Optional[str] = None

class ExecuteSqliteQuery(BaseModel):
    """Input for SQLite query execution tool"""
    db_path: str = Field(description="Path to the SQLite database file")
    query: str = Field(description="SQL query to execute")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters (for parameterized queries)")
    max_rows: Optional[int] = Field(default=None, description="Maximum number of rows to return")

class SqliteQueryResult(BaseModel):
    """Result from a single SQLite query"""
    columns: List[str] = []
    rows: List[List[Any]] = []
    row_count: int = 0
    execution_time_ms: int = 0
    affected_rows: Optional[int] = None
    is_select: bool = True
    sql_executed: str = ""

class ExecuteSqliteQueryResponse(BaseModel):
    """Response model for SQLite query execution"""
    results: List[SqliteQueryResult] = []
    error: Optional[str] = None
    is_write_operation: bool = False
    execution_time_ms: int = 0