import importlib
from typing import Dict, List, Generator, Tuple, Optional, Any

from backend.agents import BaseAgent, SQLAgentImpl
from backend.models.data_models import ChatResponse
from backend.utils import logger
from backend.config.config import config

class AgentService:
    """Service that manages agent instances and routes requests to the appropriate agent"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentService, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance._agents = {}
            cls._instance._active_agent = None
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        logger.info("Initializing Agent Service")
        
        # Register built-in agents
        self.register_agent("sql", SQLAgentImpl())
        
        # Set the active agent based on configuration
        agent_type = config.get("agent", "type", "sql")
        self.set_active_agent(agent_type)
        
        self._initialized = True
        logger.info("Agent Service initialized successfully")
    
    def register_agent(self, agent_id: str, agent: BaseAgent) -> None:
        """Register an agent with the service"""
        self._agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id} ({agent.name})")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)
    
    def set_active_agent(self, agent_id: str) -> bool:
        """Set the active agent by ID"""
        if agent_id in self._agents:
            self._active_agent = self._agents[agent_id]
            logger.info(f"Active agent set to: {agent_id} ({self._active_agent.name})")
            return True
        else:
            logger.error(f"Agent not found: {agent_id}")
            # Fall back to the first available agent
            if self._agents:
                first_agent_id = next(iter(self._agents))
                self._active_agent = self._agents[first_agent_id]
                logger.warning(f"Falling back to agent: {first_agent_id}")
                return True
            return False
    
    @property
    def active_agent(self) -> Optional[BaseAgent]:
        """Get the currently active agent"""
        return self._active_agent
    
    def get_available_agents(self) -> List[Dict[str, str]]:
        """Get a list of all available agents"""
        return [
            {"id": agent_id, "name": agent.name, "description": agent.description}
            for agent_id, agent in self._agents.items()
        ]
    
    # Core methods that pass through to the active agent
    
    def send_message(self, message_text: str, thread_id: str, user_id: str, 
                     system_message: Optional[str] = None) -> ChatResponse:
        """Send a message using the active agent"""
        if not self._active_agent:
            raise ValueError("No active agent available")
        return self._active_agent.send_message(message_text, thread_id, user_id, system_message)
    
    def stream_message(self, message_text: str, thread_id: str, user_id: str,
                       system_message: Optional[str] = None) -> Generator[Tuple[str, dict], None, None]:
        """Stream a message response from the active agent"""
        if not self._active_agent:
            raise ValueError("No active agent available")
        yield from self._active_agent.stream_message(message_text, thread_id, user_id, system_message)
    
    def get_thread(self, thread_id: str) -> Any:
        """Get a thread from the active agent"""
        if not self._active_agent:
            return None
        return self._active_agent.get_thread(thread_id)
    
    def get_threads(self, user_id: Optional[str] = None) -> List[Any]:
        """Get threads from the active agent"""
        if not self._active_agent:
            return []
        return self._active_agent.get_threads(user_id)
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread using the active agent"""
        if not self._active_agent:
            return False
        return self._active_agent.delete_thread(thread_id)


# Create a singleton instance
agent_service = AgentService()

# For backward compatibility
sql_agent = agent_service
