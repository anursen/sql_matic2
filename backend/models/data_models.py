
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class GetSqliteSchemaResponse(BaseModel):
    """Output for SQLite schema extraction tool"""
    database_schema: Dict[str, Any] = Field(..., description="The database schema information")
    tables: Optional[List[str]] = None
    error: Optional[str] = None

class ExecuteSqliteQuery(BaseModel):
    """Input for SQLite query execution tool"""
    query: str = Field(description="SQL query to execute")

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

# Performance metrics models
class PerformanceMetrics(BaseModel):
    lastQueryTime: int = 0  # in milliseconds
    averageResponseTime: float = 0  # in milliseconds
    
class TokenUsageMetrics(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0

class Metrics(BaseModel):
    performance: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    tokenUsage: TokenUsageMetrics = Field(default_factory=TokenUsageMetrics)

    def dict(self, *args, **kwargs):
        """Override dict method to ensure nested objects are also converted to dicts"""
        result = super().dict(*args, **kwargs)
        return result

# Message and Thread models for agent conversations
class Message(BaseModel):
    id: str
    text: str
    sender: str  # "user" or "bot"
    user_id: str
    timestamp: float
    
class Thread(BaseModel):
    id: str
    user_id: str
    messages: List[Message] = []
    created_at: float
    updated_at: float

# API Request/Response models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    user_id: str

class ChatResponse(BaseModel):
    text: str
    metrics: Optional[Metrics] = None
    thread_id: Optional[str] = None

class CreateThreadRequest(BaseModel):
    user_id: str


#Sqlite Metadata models
class DatabaseStats(BaseModel):
    databaseCount: int 
    tableCount: int
    rowCount: int

class TableStats(BaseModel):
    name: str
    row_count: int
    column_count: int
    index_count: int
    avg_row_size_bytes: float = 0
    estimated_size_bytes: int = 0
    estimated_size_human: str = "0 KB"
    error: Optional[str] = None

class DatabaseInfo(BaseModel):
    name: str
    path: str
    size_bytes: int = 0
    size_human: Optional[str] = None
    page_size: Optional[int] = None
    page_count: Optional[int] = None
    encoding: Optional[str] = None
    journal_mode: Optional[str] = None
    auto_vacuum: Optional[int] = None
    creation_time: Optional[str] = None
    modification_time: Optional[str] = None
    message: Optional[str] = None

class SQLiteGetMetadataResponse(BaseModel):
    database_info: DatabaseInfo
    table_stats: List[TableStats] = []
    stats: DatabaseStats = Field(default_factory=DatabaseStats)
    error: Optional[str] = None

class SqliteGetMetadataArgs(BaseModel):
    table_count: int = Field(default=0, description="Maximum number of tables to return metadata for (0 for all tables)")