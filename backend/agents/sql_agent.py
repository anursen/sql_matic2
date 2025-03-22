import time
import importlib
import pkgutil
import inspect
from typing import Dict, List, Generator, Tuple, Optional, Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from backend.agents.base_agent import BaseAgent
from backend.models.data_models import Message, Thread, ChatResponse, Metrics
from backend.utils import logger
from backend.config.config import config

class SQLAgentImpl(BaseAgent):
    """SQL Agent Implementation using LangChain"""
    
    def __init__(self):
        self._initialized = False
        self._tools = []
        self._memory = None
        self._model = None
        self._agent_executor = None
        self._metrics = None
        self._threads = {}
    
    @property
    def name(self) -> str:
        return "SQL Agent"
    
    @property
    def description(self) -> str:
        return "An agent specialized in SQL database operations and query generation"
    
    @property
    def tools(self) -> List[BaseTool]:
        return self._tools
    
    @property
    def system_message(self) -> str:
        """Get the system message from config or use the default"""
        return config.get("agent", "system_message", super().system_message)
        
    def initialize(self) -> None:
        """Initialize the agent with all necessary components"""
        if self._initialized:
            return
            
        logger.info(f"Initializing {self.name}...")
        
        # Initialize memory for persistent threads
        self._memory = MemorySaver()
        
        # Get model info from config
        model_name = config.get("agent", "model", "gpt-4")
        model_provider = config.get("agent", "provider", "openai")
        
        # Initialize the model
        self._model = init_chat_model(model_name, model_provider=model_provider)
        
        # Load all tools from the tools directory
        self._tools = self._load_tools_from_module("backend.tools")
        logger.info(f"Loaded {len(self._tools)} tools: {[tool.name for tool in self._tools]}")
        
        # Create the agent with memory
        self._agent_executor = create_react_agent(
            self._model, 
            self._tools, 
            checkpointer=self._memory
        )
        
        # Initialize metrics
        self._metrics = Metrics()
        
        self._initialized = True
        logger.info(f"{self.name} initialized successfully")
    
    def _load_tools_from_module(self, module_path: str) -> List[BaseTool]:
        """Dynamically load all tool instances from a module path"""
        tools = []
        try:
            # Import the module
            module = importlib.import_module(module_path)
            
            # Look for tool instances or functions that return tool instances
            for name in dir(module):
                if name.startswith('_'):
                    continue
                    
                attr = getattr(module, name)
                
                # Check if it's a tool instance
                if isinstance(attr, BaseTool):
                    tools.append(attr)
                # Check if it's a function that returns a tool instance
                elif inspect.isfunction(attr) and 'tool' in name.lower():
                    try:
                        tool = attr()
                        if isinstance(tool, BaseTool):
                            tools.append(tool)
                    except:
                        pass
            
            # If no tools found directly, try to import submodules
            if not tools and hasattr(module, '__path__'):
                for finder, name, ispkg in pkgutil.iter_modules(module.__path__):
                    if ispkg:
                        continue
                    # Import the submodule
                    submodule_path = f"{module_path}.{name}"
                    submodule = importlib.import_module(submodule_path)
                    
                    # Look for attributes that might be tools
                    for attr_name in dir(submodule):
                        if attr_name.startswith('_'):
                            continue
                        
                        attr = getattr(submodule, attr_name)
                        if isinstance(attr, BaseTool):
                            tools.append(attr)
        except Exception as e:
            logger.error(f"Error loading tools from {module_path}: {e}")
        
        return tools
    
    def get_or_create_thread(self, thread_id: str, user_id: str) -> Thread:
        """Get an existing thread or create a new one"""
        if thread_id not in self._threads:
            self._threads[thread_id] = Thread(
                id=thread_id,
                user_id=user_id,
                messages=[],
                created_at=time.time(),
                updated_at=time.time()
            )
        return self._threads[thread_id]

    def send_message(self, message_text: str, thread_id: str, user_id: str, 
                    system_message: Optional[str] = None) -> ChatResponse:
        """Send a message to the agent and get a response"""
        # Ensure agent is initialized
        if not self._initialized:
            self.initialize()
            
        # Get or create thread
        thread = self.get_or_create_thread(thread_id, user_id)
        
        # Create config with thread_id for memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # Record start time for metrics
        start_time = time.time()
        
        # Create messages including system message if provided
        messages = self.create_messages(message_text, system_message)
        
        # Store the human message in the thread
        thread.messages.append(Message(
            id=str(len(thread.messages)),
            text=message_text,
            sender="user",
            user_id=user_id,
            timestamp=time.time()
        ))
        
        # Update thread timestamp
        thread.updated_at = time.time()
        
        try:
            # Invoke the agent
            response = self._agent_executor.invoke(
                {"messages": messages},
                config
            )
            
            # Extract the response text
            ai_message = response["messages"][-1]
            response_text = ai_message.content
            
            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)
            
            # Update metrics
            self._update_metrics(response_time, len(message_text), len(response_text))
            
            # Store the bot's message in the thread
            thread.messages.append(Message(
                id=str(len(thread.messages)),
                text=response_text,
                sender="bot",
                user_id="SQL-Bot",
                timestamp=time.time()
            ))
            
            # Create a response object
            chat_response = ChatResponse(
                text=response_text,
                metrics=self._metrics,
                thread_id=thread_id
            )
            
            return chat_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = f"I encountered an error processing your request: {str(e)}"
            
            # Store the error message
            thread.messages.append(Message(
                id=str(len(thread.messages)),
                text=error_msg,
                sender="bot",
                user_id="SQL-Bot",
                timestamp=time.time()
            ))
            
            return ChatResponse(
                text=error_msg,
                metrics=self._metrics,
                thread_id=thread_id
            )
    
    def stream_message(self, message_text: str, thread_id: str, user_id: str,
                       system_message: Optional[str] = None) -> Generator[Tuple[str, dict], None, None]:
        """Stream a message response from the agent"""
        # Ensure agent is initialized
        if not self._initialized:
            self.initialize()
            
        # Get or create thread
        thread = self.get_or_create_thread(thread_id, user_id)
        
        # Create config with thread_id for memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # Record start time for metrics
        start_time = time.time()
        
        # Create messages including system message if provided
        messages = self.create_messages(message_text, system_message)
        
        # Store the message in the thread
        thread.messages.append(Message(
            id=str(len(thread.messages)),
            text=message_text,
            sender="user",
            user_id=user_id,
            timestamp=time.time()
        ))
        
        # Update thread timestamp
        thread.updated_at = time.time()
        
        # Add a typing indicator
        yield "typing", {"isTyping": True, "threadId": thread_id}
        
        try:
            # Collect all response text for storing in the thread
            full_response_text = ""
            
            # Stream the agent response
            for step in self._agent_executor.stream(
                {"messages": messages},
                config,
                stream_mode="values"
            ):
                # Get the latest message
                latest_message = step["messages"][-1]
                
                # If it's an AI message, yield it
                if isinstance(latest_message, AIMessage):
                    # Update the full response text
                    full_response_text = latest_message.content
                    
                    # Yield the update
                    yield "message", {
                        "text": latest_message.content,
                        "sender": "bot",
                        "userId": "SQL-Bot",
                        "timestamp": time.time(),
                        "threadId": thread_id
                    }
            
            # Calculate response time and update metrics
            response_time = int((time.time() - start_time) * 1000)
            self._update_metrics(response_time, len(message_text), len(full_response_text))
            
            # Store the bot's message in the thread
            thread.messages.append(Message(
                id=str(len(thread.messages)),
                text=full_response_text,
                sender="bot",
                user_id="SQL-Bot",
                timestamp=time.time()
            ))
            
        except Exception as e:
            logger.error(f"Error streaming message: {e}")
            error_msg = f"I encountered an error processing your request: {str(e)}"
            
            # Store the error message
            thread.messages.append(Message(
                id=str(len(thread.messages)),
                text=error_msg,
                sender="bot",
                user_id="SQL-Bot",
                timestamp=time.time()
            ))
            
            # Yield the error message
            yield "message", {
                "text": error_msg,
                "sender": "bot",
                "userId": "SQL-Bot",
                "timestamp": time.time(),
                "threadId": thread_id
            }
        finally:
            # Remove typing indicator
            yield "typing", {"isTyping": False, "threadId": thread_id}
            
            # Yield metrics update
            yield "metrics_update", {"metrics": self._metrics.dict()}
    
    def _update_metrics(self, response_time: int, prompt_length: int, completion_length: int):
        """Update agent metrics"""
        # Estimate token counts (very rough approximation)
        prompt_tokens = max(1, prompt_length // 4)
        completion_tokens = max(1, completion_length // 4)
        
        # Update timing metrics
        self._metrics.performance.lastQueryTime = response_time
        if self._metrics.performance.averageResponseTime == 0:
            self._metrics.performance.averageResponseTime = response_time
        else:
            self._metrics.performance.averageResponseTime = (
                self._metrics.performance.averageResponseTime * 0.7 + response_time * 0.3
            )
        
        # Update token usage metrics
        self._metrics.tokenUsage.prompt += prompt_tokens
        self._metrics.tokenUsage.completion += completion_tokens
        self._metrics.tokenUsage.total = self._metrics.tokenUsage.prompt + self._metrics.tokenUsage.completion
    
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID"""
        return self._threads.get(thread_id)
    
    def get_threads(self, user_id: Optional[str] = None) -> List[Thread]:
        """Get all threads, optionally filtered by user_id"""
        if user_id:
            return [thread for thread in self._threads.values() if thread.user_id == user_id]
        return list(self._threads.values())
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread by ID"""
        if thread_id in self._threads:
            del self._threads[thread_id]
            return True
        return False
