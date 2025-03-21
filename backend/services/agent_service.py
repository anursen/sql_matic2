import os
import time
from typing import Dict, List, Generator, Any, Tuple



from langchain.chat_models import init_chat_model

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from backend.models.data_models import Message, Thread, ChatResponse, Metrics
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
        self.tools = [self.search]
        
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
        """Mock SQL execution function - this would connect to a real DB in production"""
        # For testing purposes
        time.sleep(0.5)  # Simulate DB query time
        
        # Update metrics
        self.metrics.performance.lastQueryTime = 500
        self.metrics.performance.averageResponseTime = (
            self.metrics.performance.averageResponseTime * 0.7 + 500 * 0.3
        )
        
        # Mock responses for different SQL query types
        if "SELECT" in query.upper():
            return "Query executed successfully. Returned 10 rows."
        elif "CREATE TABLE" in query.upper():
            table_name = query.split("CREATE TABLE")[1].strip().split()[0]
            return f"Table {table_name} created successfully."
        elif "INSERT" in query.upper():
            return "Inserted 1 row successfully."
        elif "UPDATE" in query.upper():
            return "Updated 5 rows successfully."
        elif "DELETE" in query.upper():
            return "Deleted 2 rows successfully."
        else:
            return "Query executed successfully."
    
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
