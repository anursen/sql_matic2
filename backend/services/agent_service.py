import os
import time
from typing import Dict, List, Generator, Any, Tuple

from langchain.chat_models import init_chat_model

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from backend.models.data_models import Message, Thread, ChatResponse, Metrics
from backend.tools.sqlite_execute_query import execute_sqlite_query

def mock_search_api(query:str):
    """Search Function
    arguments:
        max_results: Maximum number of search results to return
        """
    query = "example query"
    # Simulate search results
    return [f"Result {query} for query '{query}'"]

class SQLAgent:
    """SQL Agent Service that wraps a LangChain agent"""
    
    def __init__(self):
        # Initialize memory for persistent threads
        self.memory = MemorySaver()
        
        # Initialize the LLM
        self.model = init_chat_model("gpt-4", model_provider="openai")
        
        # Initialize tools
        self.search = mock_search_api(query='2')
        
        # Create a SQL tool (this would be expanded in a real implementation)
        self.sql_tool = {
            "type": "function",
            "function": {
                "name": "execute_sql",
                "description": "Execute a SQL query against a database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to execute"
                        },
                        "database": {
                            "type": "string",
                            "description": "The database to query against"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
        
        # Combine tools
        self.tools = [self.search, execute_sqlite_query]
        
        # Create the agent with memory
        self.agent_executor = create_react_agent(
            self.model, 
            self.tools, 
            checkpointer=self.memory
        )
        
        # Thread storage
        self.threads: Dict[str, Thread] = {}
        
        # Metrics
        self.metrics = Metrics()
    
    def execute_sql(self, query: str, database: str = "default") -> str:
        """
        Execute a SQL query against the specified database.
        Now uses the execute_sqlite_query tool internally.
        """
        # Get database path from configuration
        db_config = config.get_section("query_db")
        db_path = db_config.get("path", "user_files/query_database.db")
        
        if database != "default" and os.path.exists(database):
            db_path = database
            
        # Record start time for metrics
        start_time = time.time()
        
        # Execute the query
        result = execute_sqlite_query(
            db_path=db_path,
            query=query
        )
        
        # Update metrics
        response_time = int((time.time() - start_time) * 1000)
        self.metrics.performance.lastQueryTime = response_time
        self.metrics.performance.averageResponseTime = (
            self.metrics.performance.averageResponseTime * 0.7 + response_time * 0.3
        )
        
        # Format a user-friendly response
        if result.get("error"):
            return f"Error executing query: {result['error']}"
        
        response = ""
        for query_result in result.get("results", []):
            if query_result.get("is_select", True):
                row_count = query_result.get("row_count", 0)
                response += f"Query executed successfully. Returned {row_count} rows.\n"
                
                # Include sample of results if available
                if row_count > 0:
                    columns = query_result.get("columns", [])
                    rows = query_result.get("rows", [])
                    
                    # Show column headers
                    response += "\n| " + " | ".join(columns) + " |\n"
                    response += "| " + " | ".join(["---"] * len(columns)) + " |\n"
                    
                    # Show up to 5 rows
                    for row in rows[:5]:
                        response += "| " + " | ".join([str(cell) for cell in row]) + " |\n"
                    
                    # Indicate if there are more rows
                    if row_count > 5:
                        response += f"\n... and {row_count - 5} more rows.\n"
            else:
                affected_rows = query_result.get("affected_rows", 0)
                if affected_rows is not None:
                    response += f"Query executed successfully. Affected {affected_rows} rows.\n"
                else:
                    response += "Query executed successfully.\n"
        
        return response
    
    def send_message(self, message_text: str, thread_id: str, user_id: str) -> ChatResponse:
        """Send a message to the agent and get a response"""
        # Create config with thread_id for memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # Record start time for metrics
        start_time = time.time()
        
        # Create a human message
        human_message = HumanMessage(content=message_text)
        
        # Invoke the agent
        response = self.agent_executor.invoke(
            {"messages": [human_message]},
            config
        )
        
        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)
        
        # Update metrics
        self.metrics.performance.lastQueryTime = response_time
        self.metrics.performance.averageResponseTime = (
            self.metrics.performance.averageResponseTime * 0.7 + response_time * 0.3
        )
        self.metrics.tokenUsage.prompt += 10  # This would be actual token count
        self.metrics.tokenUsage.completion += 20  # This would be actual token count
        self.metrics.tokenUsage.total = self.metrics.tokenUsage.prompt + self.metrics.tokenUsage.completion
        
        # Extract the response text
        ai_message = response["messages"][-1]
        response_text = ai_message.content
        
        # Create a response object
        chat_response = ChatResponse(
            text=response_text
        )
        
        return chat_response
    
    def stream_message(self, message_text: str, thread_id: str, user_id: str) -> Generator[Tuple[str, dict], None, None]:
        """Stream a message response from the agent"""
        # Create config with thread_id for memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # Record start time for metrics
        start_time = time.time()
        
        # Create a human message
        human_message = HumanMessage(content=message_text)
        
        # Add a typing indicator
        yield "typing", {"isTyping": True, "threadId": thread_id}
        
        # Stream the agent response
        for step in self.agent_executor.stream(
            {"messages": [human_message]},
            config,
            stream_mode="values"
        ):
            # Get the latest message
            latest_message = step["messages"][-1]
            
            # If it's an AI message, yield it
            if isinstance(latest_message, AIMessage):
                yield "message", {
                    "text": latest_message.content,
                    "sender": "bot",
                    "userId": "SQL-Bot",
                    "timestamp": time.time(),
                    "threadId": thread_id
                }
        
        # Calculate response time and update metrics
        response_time = int((time.time() - start_time) * 1000)
        self.metrics.performance.lastQueryTime = response_time
        self.metrics.performance.averageResponseTime = (
            self.metrics.performance.averageResponseTime * 0.7 + response_time * 0.3
        )
        
        # Remove typing indicator
        yield "typing", {"isTyping": False, "threadId": thread_id}
        
        # Yield metrics update
        yield "metrics_update", {"metrics": self.metrics.dict()}

# Create a singleton instance
sql_agent = SQLAgent()
