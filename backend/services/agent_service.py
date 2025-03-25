from typing import Dict, Any, List, Tuple, Optional, Generator, AsyncGenerator
import uuid
from datetime import datetime
import importlib
import inspect
import json

from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from backend.utils.logger import get_logger
from backend.config.config import config
from backend.models.data_models import (
    AgentInfo, AgentMetrics, AgentConfig, AgentToolCall, 
    AgentPerformanceMetrics, AgentTokenUsage, AgentToolUsage,
    DatabaseStatsMetrics, StreamMessageRequest
)

logger = get_logger(__name__)

class Agent:
    """
    Represents an AI agent with tools and capabilities.
    """
    
    def __init__(self, name: str, description: str, agent_type: str, tools: Optional[List[Tool]] = None, 
                 model=None, memory=None, agent_executor=None):
        """
        Initialize an agent with tools.
        
        Args:
            name: Name of the agent
            description: Description of the agent's capabilities
            agent_type: Type of agent (sql, evaluator, etc.)
            tools: List of tools the agent can use
            model: Language model for the agent
            memory: Memory instance for maintaining conversation state
            agent_executor: The LangGraph agent executor
        """
        self.name = name
        self.description = description
        self.agent_type = agent_type
        self.tools = tools or []
        self.id = str(uuid.uuid4())
        self.model = model
        self.memory = memory
        self.agent_executor = agent_executor
        self.system_message_content = ""  # Added field to store system message
        logger.info(f"Created agent: {name} ({agent_type}) with {len(self.tools)} tools")
    
    def add_tool(self, tool: Tool):
        """Add a tool to the agent."""
        self.tools.append(tool)
        logger.info(f"Added tool {tool.name} to agent {self.name}")


class AgentService:
    """
    Service for managing AI agents and their interactions.
    """
    
    def __init__(self):
        """Initialize the agent service."""
        self.active_agent = None
        self.agents: Dict[str, Agent] = {}
        self.memory_store = MemorySaver()  # Shared memory store for agents
        self._load_agents()
        logger.info("AgentService initialized")
    
    # Replace the existing _load_tool method with this more flexible version
    def _load_tool(self, tool_name: str) -> Optional[Tool]:
        """Load a tool by name directly from the tools package."""
        try:
            # First try direct import by function name
            if tool_name == "sqlite_execute_query":
                from backend.tools.sqlite_execute_query import sqlite_execute_query
                return sqlite_execute_query
            elif tool_name == "sqlite_get_schema":
                from backend.tools.sqlite_get_schema import sqlite_get_schema
                return sqlite_get_schema
            elif tool_name == "sqlite_get_metadata":
                from backend.tools.sqlite_get_metadata import sqlite_get_metadata
                return sqlite_get_metadata
                
            # If direct import doesn't work, fall back to the original logic
            module_path = f"backend.tools.{tool_name}"
            module = importlib.import_module(module_path)

        except ImportError as e:
            # If direct import fails, try importing from subdirectories
            subdirs = ["sqlite"]
            for subdir in subdirs:
                try:
                    alt_module_path = f"backend.tools.{subdir}.{tool_name}"
                    module = importlib.import_module(alt_module_path)
                    logger.info(f"Imported module {alt_module_path}")
                    
                    # Try to get the function with the same name
                    if hasattr(module, tool_name):
                        tool_function = getattr(module, tool_name)
                        if callable(tool_function) and hasattr(tool_function, '_tool'):
                            logger.info(f"Loaded tool {tool_name} from {alt_module_path}")
                            return tool_function
                    
                    # Look for any function with @tool decorator
                    for name, obj in inspect.getmembers(module):
                        if inspect.isfunction(obj) and hasattr(obj, '_tool'):
                            logger.info(f"Loaded tool {name} from {alt_module_path}")
                            return obj
                except ImportError:
                    continue
            
            logger.error(f"Could not import tool {tool_name}: {e}")
            return None
                
        except Exception as e:
            logger.error(f"Error loading tool {tool_name}: {str(e)}")
            return None
    
    def _create_llm(self, agent_config: Dict[str, Any]):
        """
        Create a language model based on configuration.
        
        Args:
            agent_config: Configuration for the agent
            
        Returns:
            The initialized language model
        """
        provider = agent_config.get("provider", "openai")
        model_name = agent_config.get("model", "gpt-4")
        temperature = agent_config.get("temperature", 0.7)
        max_tokens = agent_config.get("max_tokens", 1000)
        
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:  # default to OpenAI
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
    
    def _load_agents(self):
        """Load agents based on configuration."""
        try:
            agent_config = config.get_section("agent")
            if not agent_config:
                logger.warning("No agent configuration found")
                return
            
            default_type = agent_config.get("default_type", "sql")
            agent_types = agent_config.get("types", {})
            
            for agent_type, type_config in agent_types.items():
                # Get configuration for this agent type
                system_message_content = type_config.get("system_message", "")
                
                # Store system message content for later use when invoking
                if system_message_content:
                    logger.info(f"Stored system message for agent type {agent_type}")
                
                # Load tools for this agent type
                tools = []
                tool_names = type_config.get("tools", [])
                
                # Convert string to list if needed
                if isinstance(tool_names, str):
                    tool_names = [name.strip() for name in tool_names.replace('\n', ',').split(',') if name.strip()]
                
                # Load available tools
                for tool_name in tool_names:
                    tool = self._load_tool(tool_name)
                    if tool:
                        tools.append(tool)
                
                # Create language model
                model = self._create_llm(type_config)
                
                # Create agent - even without tools
                try:
                    # Create without system message parameter
                    agent_executor = create_react_agent(
                        model=model,
                        tools=tools,
                        checkpointer=self.memory_store
                    )
                    
                    # Create and register the agent
                    agent = Agent(
                        name=f"{agent_type.capitalize()} Assistant",
                        description=f"An AI assistant specialized in {agent_type} tasks",
                        agent_type=agent_type,
                        tools=tools,
                        model=model,
                        memory=self.memory_store,
                        agent_executor=agent_executor
                    )
                    print("Agent executor created {agent}")    
                    # Store the system message content in the agent for later use
                    agent.system_message_content = system_message_content
                    
                    self.register_agent(agent)
                    
                    # Set as active if it's the default type
                    if agent_type == default_type:
                        self.set_active_agent(agent.id)
                        
                    logger.info(f"Successfully created agent: {agent_type} with {len(tools)} tools")
                    
                except Exception as agent_error:
                    logger.error(f"Error creating agent {agent_type}: {str(agent_error)}")
            
            logger.info(f"Loaded {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to load agents: {str(e)}")
    
    def register_agent(self, agent: Agent):
        """
        Register an agent with the service.
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.id] = agent
        logger.info(f"Registered agent {agent.name} with ID {agent.id}")
    
    def set_active_agent(self, agent_id: str):
        """
        Set the active agent by ID.
        
        Args:
            agent_id: ID of the agent to set as active
        
        Returns:
            bool: True if successful, False if agent not found
        """
        if agent_id in self.agents:
            self.active_agent = self.agents[agent_id]
            logger.info(f"Set active agent to {self.active_agent.name}")
            return True
        logger.warning(f"Agent with ID {agent_id} not found")
        return False
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent to get
        
        Returns:
            Agent: The agent if found, None otherwise
        """
        return self.agents.get(agent_id)
    
    def get_available_agents(self) -> List[AgentInfo]:
        """
        Get list of available agents.
        
        Returns:
            List[AgentInfo]: List of agent information
        """
        return [
            AgentInfo(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                type=agent.agent_type,
                tools=[tool.name for tool in agent.tools]
            )
            for agent in self.agents.values()
        ]
    
    def process_message(self, message_text: str, thread_id: str, 
                        user_id: Optional[str] = None, 
                        agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and get an AI response.
        
        Args:
            message_text: User message text
            thread_id: Thread identifier
            user_id: Optional user identifier
            agent_id: Optional agent ID to use (uses active agent if not specified)
            
        Returns:
            Dict[str, Any]: Response with AI message and metadata
        """
        try:
            # Get the specified agent or fall back to active agent
            if agent_id:
                agent = self.agents.get(agent_id)
                if not agent:
                    logger.warning(f"Agent with ID {agent_id} not found, falling back to active agent")
                    agent = self.active_agent
            else:
                agent = self.active_agent
                
            if not agent:
                raise ValueError("No agent available to process message")
            
            logger.info(f"Processing message in thread {thread_id} with agent {agent.name} (ID: {agent.id})")
            
            # Include system message if available
            messages = []
            if hasattr(agent, 'system_message_content') and agent.system_message_content:
                messages.append(SystemMessage(content=agent.system_message_content))
            
            # Add the user message
            messages.append(HumanMessage(content=message_text))
            
            # Create the input for the agent with messages
            agent_input = {
                "messages": messages
            }
            
            # Configure the agent execution with thread_id for memory management
            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }
            
            # Execute the agent
            logger.info(f"Invoking agent_executor with messages: {messages}")
            # Use invoke method which follows the pattern in agents.ipynb
            result = agent.agent_executor.invoke(agent_input, config)
            logger.info(f"Agent result: {result}")
            
            # Extract the result
            messages = result.get("messages", [])
            last_message = messages[-1] if messages else None
            
            # Check if the last message has content
            content = ""
            if last_message:
                if hasattr(last_message, 'content'):
                    content = last_message.content
                    # Handle if content is None or not a string
                    if content is None:
                        content = "No content in response"
                    elif not isinstance(content, str):
                        # Try to convert complex content to string representation
                        try:
                            content = str(content)
                        except:
                            content = "Complex response that couldn't be converted to text"
                else:
                    content = "Response has no content attribute"
            else:
                content = "No response generated"
                
            # Log tool calls if present
            tool_calls = getattr(last_message, 'tool_calls', [])
            if tool_calls:
                logger.info(f"Tool calls in response: {tool_calls}")
            
            # Prepare response without metrics
            response = {
                "message": {
                    "id": str(uuid.uuid4()),
                    "content": content,
                    "role": "assistant",
                    "created_at": datetime.now().isoformat()
                },
                "thread_id": thread_id,
                # Empty metrics object for now
                "metrics": {}
            }
            
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    def stream_message(self, message_text: str, thread_id: str,
                      user_id: Optional[str] = None,
                      agent_id: Optional[str] = None) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """
        Stream a response to a user message.
        
        Args:
            message_text: User message text
            thread_id: Thread identifier
            user_id: Optional user identifier
            agent_id: Optional agent ID to use
            
        Yields:
            Tuple[str, Dict[str, Any]]: Event type and event data
        """
        try:
            # Initialize metrics collection
            metrics = AgentMetrics(
                tokenUsage=AgentTokenUsage(),
                performance=AgentPerformanceMetrics(
                    startTime=datetime.now().timestamp() * 1000
                ),
                toolUsage=AgentToolUsage(),
                databaseStats=DatabaseStatsMetrics()
            )
            
            # Validate message - don't process empty messages
            if not message_text or message_text.strip() == "":
                logger.warning(f"Received empty message in thread {thread_id}")
                yield "error", {
                    "message": "Please provide a valid message. Your message appears to be empty.",
                    "thread_id": thread_id
                }
                return
                
            # Get the specified agent or fall back to active agent
            if agent_id:
                agent = self.agents.get(agent_id)
                if not agent:
                    logger.warning(f"Agent with ID {agent_id} not found, falling back to active agent")
                    agent = self.active_agent
            else:
                agent = self.active_agent
                
            if not agent:
                raise ValueError("No agent available to process message")
            
            logger.info(f"Streaming message response in thread {thread_id} with agent {agent.name} (ID: {agent.id})")
            
            # First yield the user message event
            yield "chat_message", {
                "message": {
                    "id": str(uuid.uuid4()),
                    "content": message_text,
                    "role": "user",
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat()
                },
                "thread_id": thread_id
            }
            
            # Include system message if available
            messages = []
            if hasattr(agent, 'system_message_content') and agent.system_message_content:
                messages.append(SystemMessage(content=agent.system_message_content))
            
            # Add the user message
            messages.append(HumanMessage(content=message_text))
            
            # Prepare input for the agent with messages - follow agents.ipynb pattern
            agent_input = {
                "messages": messages
            }
            
            # Configure the agent execution with thread_id for memory
            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }
            
            # Signal that typing has started
            yield "typing_indicator", {"isTyping": True}
            
            # Stream the agent execution
            message_id = str(uuid.uuid4())
            full_content = ""
            query_count = 0
            rows_returned = 0
            
            logger.info(f"Streaming with agent_executor using messages: {messages}")
            # Use the stream method with "values" as shown in agents.ipynb
            for step in agent.agent_executor.stream(agent_input, config, stream_mode="values"):
                logger.info(f"Stream step: {step}")
                if "messages" in step and step["messages"]:
                    message = step["messages"][-1]
                    
                    # Collect token usage metrics from response metadata if available
                    if hasattr(message, 'response_metadata') and message.response_metadata:
                        meta = message.response_metadata
                        if 'token_usage' in meta:
                            token_usage = meta['token_usage']
                            if 'prompt_tokens' in token_usage:
                                metrics.tokenUsage.prompt += token_usage.get('prompt_tokens', 0)
                            if 'completion_tokens' in token_usage:
                                metrics.tokenUsage.completion += token_usage.get('completion_tokens', 0)
                            if 'total_tokens' in token_usage:
                                metrics.tokenUsage.total += token_usage.get('total_tokens', 0)
                    
                    # Also check usage_metadata which might have more detailed info
                    if hasattr(message, 'usage_metadata') and message.usage_metadata:
                        usage = message.usage_metadata
                        if 'input_tokens' in usage:
                            metrics.tokenUsage.prompt += usage.get('input_tokens', 0)
                        if 'output_tokens' in usage:
                            metrics.tokenUsage.completion += usage.get('output_tokens', 0)
                        if 'total_tokens' in usage:
                            metrics.tokenUsage.total += usage.get('total_tokens', 0)
                    
                    if isinstance(message, AIMessage):
                        # Extract content - handle various content formats
                        if hasattr(message, 'content'):
                            content = message.content
                            if content and isinstance(content, str):
                                # Get the new content (what was added since last chunk)
                                new_content = content[len(full_content):]
                                full_content = content
                                
                                if new_content:
                                    yield "token_stream", {
                                        "token": new_content,
                                        "message_id": message_id,
                                        "thread_id": thread_id,
                                        "is_complete": False
                                    }
                        
                        # Check for tool calls and log them
                        tool_calls = getattr(message, 'tool_calls', [])
                        if tool_calls:
                            logger.info(f"Tool calls in streaming response: {tool_calls}")
                            
                            # Track tool usage in metrics
                            for tool_call in tool_calls:
                                metrics.toolUsage.totalCalls += 1
                                tool_name = tool_call.get('name', 'unknown')
                                
                                # Record details about this tool call
                                tool_info = AgentToolCall(
                                    name=tool_name,
                                    args=tool_call.get('args', {}),
                                    timestamp=datetime.now().isoformat()
                                )
                                
                                # Set as last used tool
                                metrics.toolUsage.lastUsed = tool_info
                                
                                # Add to the list of tools called
                                metrics.toolUsage.tools.append(tool_info)
                            
                            # You could also yield tool calls as a separate event if needed
                            yield "tool_calls", {
                                "tool_calls": tool_calls,
                                "message_id": message_id,
                                "thread_id": thread_id
                            }
                    
                    # Check for tool message responses to collect DB stats
                    elif isinstance(message, ToolMessage):
                        # Track tool result
                        if hasattr(message, 'name') and message.name:
                            # Update last used tool with results info
                            if metrics.toolUsage.lastUsed and metrics.toolUsage.lastUsed.name == message.name:
                                metrics.toolUsage.lastUsed.result_received = True
                                metrics.toolUsage.lastUsed.result_timestamp = datetime.now().isoformat()
                        
                        # Try to parse JSON content for database metrics
                        try:
                            if hasattr(message, 'content') and message.content:
                                # Check if this is a database query result
                                if message.name == 'sqlite_execute_query':
                                    query_count += 1
                                    metrics.databaseStats.queryCount = query_count
                                    
                                    # Try to parse the content as JSON
                                    content_data = json.loads(message.content)
                                    
                                    # Get execution time if available
                                    if 'execution_time_ms' in content_data:
                                        metrics.performance.dbTime += content_data.get('execution_time_ms', 0)
                                    
                                    # Count rows returned
                                    if 'results' in content_data:
                                        results = content_data['results']
                                        if isinstance(results, list):
                                            for result in results:
                                                if 'row_count' in result:
                                                    rows_returned += result.get('row_count', 0)
                                                elif 'rows' in result and isinstance(result['rows'], list):
                                                    rows_returned += len(result['rows'])
                                    
                                    metrics.databaseStats.rowsReturned = rows_returned
                                
                                # Check if this is a schema query result to count tables
                                elif message.name == 'sqlite_get_schema':
                                    # Try to extract table count from schema result
                                    if 'tables=' in message.content:
                                        tables_data = message.content.split('tables=')[1].split(']')[0] + ']'
                                        # Count table entries in the schema output
                                        table_count = tables_data.count('TableInfo(name=')
                                        metrics.databaseStats.tableCount = table_count
                        except Exception as parse_error:
                            logger.warning(f"Error parsing tool message content: {str(parse_error)}")
            
            # If we didn't get any content, provide a fallback
            if not full_content:
                full_content = "I processed your request, but couldn't generate a proper response."
            
            # Calculate final performance metrics
            metrics.performance.endTime = datetime.now().timestamp() * 1000
            metrics.performance.totalTime = metrics.performance.endTime - metrics.performance.startTime
            # Estimate LLM time (total time minus DB time)
            metrics.performance.llmTime = metrics.performance.totalTime - metrics.performance.dbTime
            
            # Send complete message event - but don't repeat the content that was already streamed
            # Just send a completion event with is_complete=true and empty content
            yield "token_stream", {
                "token": "",
                "message_id": message_id,
                "thread_id": thread_id,
                "is_complete": True,
                "full_content": full_content  # Include the full content for reference
            }
            
            # Send typing indicator off event
            yield "typing_indicator", {"isTyping": False}
            
            # Send metrics event
            yield "metrics", metrics.dict()
            
        except Exception as e:
            logger.error(f"Error streaming message: {str(e)}")
            # Send error event
            yield "error", {
                "message": f"Error: {str(e)}",
                "thread_id": thread_id
            }
            # Turn off typing indicator
            yield "typing_indicator", {"isTyping": False}
    
    async def astream_message(self, message_text: str, thread_id: str,
                           user_id: Optional[str] = None, 
                           agent_id: Optional[str] = None) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """
        Async version of stream_message.
        
        Args:
            message_text: User message text
            thread_id: Thread identifier
            user_id: Optional user identifier
            agent_id: Optional agent ID to use
            
        Yields:
            Tuple[str, Dict[str, Any]]: Event type and event data
        """
        # This is a wrapper to make the sync generator async
        for event_type, event_data in self.stream_message(
            message_text, thread_id, user_id, agent_id
        ):
            yield event_type, event_data

agent_service = AgentService()