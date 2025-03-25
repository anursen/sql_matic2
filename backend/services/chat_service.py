from typing import List, Dict, Any, Optional, AsyncGenerator
import uuid
from datetime import datetime

from backend.services.db_service import ChatDBService
from backend.services.thread_service import ThreadService, get_thread_service
from backend.models.data_models import (
    ChatMessage, 
    ChatThread, 
    ChatThreadList,
    ChatThreadSummary,
    CreateThreadRequest,
    AddMessageRequest
)
from backend.utils.logger import get_logger
from backend.config.config import config

logger = get_logger(__name__)

class ChatService:
    """
    Service for managing chat interactions and history.
    Handles business logic related to chat functionality.
    """
    
    def __init__(self, db_service: Optional[ChatDBService] = None, thread_service: Optional[ThreadService] = None):
        """
        Initialize chat service with DB service.
        
        Args:
            db_service: Database service for chat persistence
            thread_service: Thread service for thread management
        """
        self.db_service = db_service
        self.thread_service = thread_service or get_thread_service()
        logger.info("ChatService initialized")
    
    async def get_or_create_user_thread(self, user_id: str) -> str:
        """Get existing thread for user or create a new one."""
        return self.thread_service.get_or_create_user_thread(user_id)
    
    async def create_thread(self, request: CreateThreadRequest) -> ChatThread:
        """
        Create a new chat thread.
        
        Args:
            request: Thread creation request containing user_id, title, etc.
            
        Returns:
            ChatThread: The created thread
        """
        try:
            thread = self.thread_service.create_thread(request)
            
            # Add system message if provided
            if request.system_message:
                await self.add_message(AddMessageRequest(
                    thread_id=thread.id,
                    role="system",
                    content=request.system_message,
                    user_id=request.user_id
                ))
                
            logger.info(f"Created new chat thread {thread.id} for user {request.user_id}")
            return thread
        except Exception as e:
            logger.error(f"Failed to create chat thread: {str(e)}")
            raise
    
    async def get_thread(self, thread_id: str, with_messages: bool = True) -> Optional[ChatThread]:
        """
        Get a thread by ID.
        
        Args:
            thread_id: Thread identifier
            with_messages: Whether to include messages
            
        Returns:
            ChatThread: The thread if found, None otherwise
        """
        try:
            thread = self.thread_service.get_thread(thread_id)
            if thread and with_messages:
                # Get messages from thread service
                messages = await self.get_messages(thread_id)
                thread.messages = messages
            return thread
        except Exception as e:
            logger.error(f"Failed to get chat thread {thread_id}: {str(e)}")
            raise
    
    async def list_threads(self, user_id: str, page: int = 1, 
                           page_size: int = 20) -> ChatThreadList:
        """
        List threads for a user.
        
        Args:
            user_id: User identifier
            page: Page number
            page_size: Threads per page
            
        Returns:
            ChatThreadList: List of thread summaries
        """
        try:
            thread_list = self.thread_service.list_threads(user_id)
            return thread_list
        except Exception as e:
            logger.error(f"Failed to list chat threads for user {user_id}: {str(e)}")
            raise
    
    async def delete_thread(self, thread_id: str) -> bool:
        """
        Delete a thread.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            bool: Success status
        """
        try:
            success = self.thread_service.delete_thread(thread_id)
            return success
        except Exception as e:
            logger.error(f"Failed to delete chat thread {thread_id}: {str(e)}")
            raise
    
    async def add_message(self, request: AddMessageRequest) -> ChatMessage:
        """
        Add a message to a thread.
        
        Args:
            request: Message creation request
            
        Returns:
            ChatMessage: The created message
        """
        try:
            # Ensure thread exists for this user
            if request.user_id and not request.thread_id:
                thread_id = self.thread_service.get_or_create_user_thread(request.user_id)
                request.thread_id = thread_id
            
            # Create message
            message_id = str(uuid.uuid4())
            now = datetime.now()
            message = ChatMessage(
                id=message_id,
                thread_id=request.thread_id,
                role=request.role,
                content=request.content,
                created_at=now,
                user_id=request.user_id,
                metadata=request.metadata
            )
            
            # Add to thread
            self.thread_service.add_message_to_thread(request.thread_id, message)
            
            # If DB service exists, also store there
            if self.db_service:
                try:
                    self.db_service.add_message(
                        request.thread_id, 
                        request.role, 
                        request.content,
                        request.user_id,
                        request.metadata
                    )
                except Exception as e:
                    logger.warning(f"Failed to store message in DB: {e}. Using in-memory only.")
            
            return message
        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}")
            raise
    
    async def get_messages(self, thread_id: str, limit: int = 100) -> List[ChatMessage]:
        """
        Get messages from a thread.
        
        Args:
            thread_id: Thread identifier
            limit: Maximum messages to return
            
        Returns:
            List[ChatMessage]: Thread messages
        """
        try:
            # Get messages from thread service
            messages = self.thread_service.get_messages(thread_id, limit)
            return messages
        except Exception as e:
            logger.error(f"Failed to get messages for thread {thread_id}: {str(e)}")
            raise
    
    async def search_threads(self, user_id: str, query: str, 
                             page: int = 1, page_size: int = 20) -> ChatThreadList:
        """
        Search for threads by title or message content.
        In this implementation, we just return the user's thread if the query appears in title or messages.
        
        Args:
            user_id: User identifier
            query: Search query string
            page: Page number
            page_size: Threads per page
            
        Returns:
            ChatThreadList: List of matching thread summaries
        """
        try:
            # For now, just return the user's thread
            # In a more complete implementation, would search message content
            return await self.list_threads(user_id, page, page_size)
        except Exception as e:
            logger.error(f"Failed to search threads for user {user_id}: {str(e)}")
            raise
    
    async def update_thread_title(self, thread_id: str, title: str) -> bool:
        """
        Update the title of a thread.
        
        Args:
            thread_id: Thread identifier
            title: New title
            
        Returns:
            bool: Success status
        """
        try:
            success = self.thread_service.update_thread_title(thread_id, title)
            return success
        except Exception as e:
            logger.error(f"Failed to update title for thread {thread_id}: {str(e)}")
            raise

# Create a default service instance for dependency injection
_default_chat_service = None

def get_chat_service():
    global _default_chat_service
    if _default_chat_service is None:
        _default_chat_service = ChatService()
    return _default_chat_service
