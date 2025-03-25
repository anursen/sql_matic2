from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

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
    title: str = Field(..., description="Title for the new thread")
    system_message: Optional[str] = Field(None, description="Optional system message to initialize the thread")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the thread")

class AddMessageRequest(BaseModel):
    """Request to add a message to a thread."""
    thread_id: str = Field(..., description="Thread identifier")
    role: str = Field(..., description="Role of the message (user/assistant/system)")
    content: str = Field(..., description="Content of the message")
    user_id: Optional[str] = Field(None, description="User identifier for user messages")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

# Enhanced chat history models
class ChatMessage(BaseModel):
    """Represents a single message in a chat thread."""
    id: str = Field(..., description="Unique message identifier")
    thread_id: str = Field(..., description="Thread this message belongs to")
    role: str = Field(..., description="Role of the message sender (user/assistant/system)")
    content: str = Field(..., description="Content of the message")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when message was created")
    user_id: Optional[str] = Field(None, description="User identifier for user messages")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the message")

class ChatThread(BaseModel):
    """Represents a chat thread containing multiple messages."""
    id: str = Field(..., description="Unique thread identifier")
    user_id: str = Field(..., description="User who owns this thread")
    title: str = Field(..., description="Title of the chat thread")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when thread was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp when thread was last updated")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the thread")
    messages: Optional[List[ChatMessage]] = Field(None, description="Messages in this thread")

class ChatThreadSummary(BaseModel):
    """Summary of a chat thread without detailed messages."""
    id: str = Field(..., description="Unique thread identifier")
    user_id: str = Field(..., description="User who owns this thread")
    title: str = Field(..., description="Title of the chat thread") 
    created_at: datetime = Field(..., description="Timestamp when thread was created")
    updated_at: datetime = Field(..., description="Timestamp when thread was last updated")
    message_count: int = Field(0, description="Number of messages in the thread")
    last_message_preview: Optional[str] = Field(None, description="Preview of the last message")

class ChatThreadList(BaseModel):
    """List of chat threads with pagination support."""
    threads: List[ChatThreadSummary] = Field(default_factory=list, description="List of thread summaries")
    total: int = Field(..., description="Total number of threads available")
    has_more: bool = Field(default=False, description="Whether there are more threads to fetch")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Number of threads per page")

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


#Sqlite Get Schema models
class GetSqliteSchemaRequest(BaseModel):
    """Request model for the SQLite schema extraction tool."""
    table_count: int = Field(default=0, description="Limit the number of tables to return (0 for all)")

class ColumnInfo(BaseModel):
    """Information about a database column."""
    name: str = Field(description="Name of the column")
    data_type: str = Field(description="SQL data type of the column")
    is_primary_key: bool = Field(description="Whether the column is a primary key")
    is_foreign_key: bool = Field(description="Whether the column is a foreign key")
    references: Optional[str] = Field(None, description="Reference information (table.column) if foreign key")


class TableInfo(BaseModel):
    """Information about a database table."""
    name: str = Field(description="Name of the table")
    columns: List[ColumnInfo] = Field(default_factory=list, description="List of columns in the table")


class GetSqliteSchemaResponse(BaseModel):
    """Response model for the SQLite schema extraction tool."""
    database_path: str = Field(description="Path to the SQLite database file")
    tables: List[TableInfo] = Field(default_factory=list, description="List of tables in the database")
    error: Optional[str] = Field(None, description="Error message if schema extraction failed")


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

# Agent-related models
class ToolInfo(BaseModel):
    """Information about a tool used by an agent."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    args_schema: Optional[Dict[str, Any]] = Field(None, description="Schema for the tool's arguments")

class AgentToolCall(BaseModel):
    """Representation of a tool call made by an agent."""
    name: str = Field(..., description="Name of the tool called")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When the tool was called")
    result_received: bool = Field(False, description="Whether a result was received from the tool")
    result_timestamp: Optional[str] = Field(None, description="When the result was received")

class AgentToolUsage(BaseModel):
    """Information about tool usage during agent execution."""
    totalCalls: int = Field(0, description="Total number of tool calls made")
    tools: List[AgentToolCall] = Field(default_factory=list, description="List of tools called")
    lastUsed: Optional[AgentToolCall] = Field(None, description="The last tool used")

class DatabaseStatsMetrics(BaseModel):
    """Metrics related to database usage."""
    queryCount: int = Field(0, description="Number of queries executed")
    rowsReturned: int = Field(0, description="Total number of rows returned")
    tableCount: int = Field(0, description="Number of tables in the database")
    databaseCount: int = Field(0, description="Number of databases accessed")

class AgentPerformanceMetrics(BaseModel):
    """Detailed performance metrics for agent execution."""
    startTime: float = Field(..., description="Start time in milliseconds")
    endTime: float = Field(0, description="End time in milliseconds")
    totalTime: float = Field(0, description="Total execution time in milliseconds")
    llmTime: float = Field(0, description="Time spent in LLM processing in milliseconds")
    dbTime: float = Field(0, description="Time spent in database operations in milliseconds")

class AgentTokenUsage(BaseModel):
    """Token usage information for an agent interaction."""
    prompt: int = Field(0, description="Number of tokens used in the prompt")
    completion: int = Field(0, description="Number of tokens used in the completion")
    total: int = Field(0, description="Total number of tokens used")

class AgentMetrics(BaseModel):
    """Complete metrics for an agent execution."""
    tokenUsage: AgentTokenUsage = Field(default_factory=AgentTokenUsage, description="Token usage metrics")
    performance: AgentPerformanceMetrics = Field(..., description="Performance timing metrics")
    toolUsage: AgentToolUsage = Field(default_factory=AgentToolUsage, description="Tool usage metrics")
    databaseStats: Optional[DatabaseStatsMetrics] = Field(default_factory=DatabaseStatsMetrics, description="Database statistics")

class AgentConfig(BaseModel):
    """Configuration for an agent."""
    provider: str = Field("openai", description="LLM provider (openai, anthropic, etc.)")
    model: str = Field("gpt-4", description="Model name to use")
    temperature: float = Field(0.7, description="Temperature for LLM sampling")
    max_tokens: int = Field(1000, description="Maximum tokens for LLM response")
    system_message: Optional[str] = Field("", description="System message for the agent")
    tools: List[str] = Field(default_factory=list, description="List of tool names for this agent")

class AgentInfo(BaseModel):
    """Information about an available agent."""
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of the agent's capabilities")
    type: str = Field(..., description="Type of agent (sql, evaluator, etc.)")
    tools: Optional[List[str]] = Field(None, description="List of tool names available to this agent")

class StreamEvent(BaseModel):
    """An event in the agent streaming response."""
    type: str = Field(..., description="Type of the event (token_stream, tool_calls, etc.)")
    payload: Dict[str, Any] = Field(..., description="Payload of the event")

class StreamMessageRequest(BaseModel):
    """Request for streaming a message through an agent."""
    message_text: str = Field(..., description="Text of the user message")
    thread_id: str = Field(..., description="Thread identifier")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    agent_id: Optional[str] = Field(None, description="Optional agent ID to use")

# Agent Request/Response models (clarified and updated)
class AgentChatRequest(BaseModel):
    """Request model for agent chat endpoint."""
    message: str = Field(..., description="Message text to send to the agent")
    thread_id: Optional[str] = Field(None, description="Thread identifier, will be generated if not provided")
    user_id: Optional[str] = Field(None, description="User identifier")
    agent_id: Optional[str] = Field(None, description="Agent identifier to use for this request")

class AgentInfo(BaseModel):
    """Information about an agent."""
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of what the agent does")
    type: str = Field(..., description="Type of the agent")
    tools: Optional[List[ToolInfo]] = Field(None, description="Tools available to this agent")

# Message and Thread models specifically for agent conversations
class AgentMessage(BaseModel):
    """Represents a message in an agent conversation."""
    id: str = Field(..., description="Unique message identifier")
    text: str = Field(..., description="Message content")
    sender: str = Field(..., description="Sender of the message (user/bot)")
    user_id: str = Field(..., description="User associated with this message")
    timestamp: float = Field(..., description="Timestamp when message was sent")
    
class AgentThread(BaseModel):
    """Represents a thread of conversation with an agent."""
    id: str = Field(..., description="Unique thread identifier")
    user_id: str = Field(..., description="User who owns this thread")
    messages: List[AgentMessage] = Field(default_factory=list, description="Messages in this thread")
    created_at: float = Field(..., description="Timestamp when thread was created")
    updated_at: float = Field(..., description="Timestamp when thread was last updated")

# Add this model for the update thread title endpoint
class UpdateThreadTitleRequest(BaseModel):
    """Request to update a thread's title."""
    title: str = Field(..., description="New title for the thread")

# WebSocket Message Models
class WebSocketMessage(BaseModel):
    """Base model for WebSocket messages."""
    type: str = Field(..., description="Type of message")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload")

class WebSocketChatMessage(BaseModel):
    """Model for chat messages sent over WebSocket."""
    message: str = Field(..., description="Message text")
    thread_id: Optional[str] = Field(None, description="Thread identifier")
    user_id: Optional[str] = Field(None, description="User identifier")

class WebSocketAgentMessage(BaseModel):
    """Model for agent messages sent over WebSocket."""
    message: str = Field(..., description="Message text")
    thread_id: Optional[str] = Field(None, description="Thread identifier")
    user_id: Optional[str] = Field(None, description="User identifier") 
    agent_id: Optional[str] = Field(None, description="Agent identifier")

class WebSocketResponse(BaseModel):
    """Model for WebSocket responses."""
    type: str = Field(..., description="Type of response")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Response payload")

class WebSocketConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""
    client_id: str = Field(..., description="Client identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    thread_id: Optional[str] = Field(None, description="Thread identifier")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    connected_at: datetime = Field(default_factory=datetime.now, description="Connection time")
