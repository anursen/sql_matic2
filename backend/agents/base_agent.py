import abc
from typing import List, Generator, Tuple, Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage

class BaseAgent(abc.ABC):
    """Abstract base class for all agent implementations"""
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of this agent"""
        pass
    
    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Return a description of this agent's capabilities"""
        pass
    
    @property
    @abc.abstractmethod
    def tools(self) -> List[BaseTool]:
        """Return the list of tools available to this agent"""
        pass
    
    @property
    def system_message(self) -> str:
        """Return the system message to guide agent behavior"""
        return """You are SQL Matic, an AI assistant specialized in helping with SQL database operations. 
        Answer questions about databases, help write SQL queries, and explain database concepts.
        When generating SQL code, follow best practices and prioritize clarity.
        If you're unsure about the schema or data, use the tools provided to gather information."""
        
    @abc.abstractmethod
    def initialize(self) -> None:
        """Initialize the agent with necessary models and tools"""
        pass
    
    @abc.abstractmethod
    def send_message(self, message_text: str, thread_id: str, user_id: str, 
                    system_message: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to the agent and get a response"""
        pass
        
    @abc.abstractmethod
    def stream_message(self, message_text: str, thread_id: str, user_id: str, 
                      system_message: Optional[str] = None) -> Generator[Tuple[str, dict], None, None]:
        """Stream a message response from the agent"""
        pass
        
    def create_messages(self, message_text: str, system_message: Optional[str] = None) -> List[Any]:
        """Create the message list including the system message"""
        messages = []
        
        # Add system message if provided, otherwise use the default
        if system_message is not None:
            messages.append(SystemMessage(content=system_message))
        elif self.system_message:
            messages.append(SystemMessage(content=self.system_message))
            
        # Add the human message
        messages.append(HumanMessage(content=message_text))
        
        return messages
