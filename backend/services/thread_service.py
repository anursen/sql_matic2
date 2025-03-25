import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.models.data_models import (
    ChatThread,
    ChatThreadList,
    ChatThreadSummary,
    CreateThreadRequest
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class ThreadService:
    """
    Service for managing chat threads.
    Provides in-memory storage of threads with one thread per user.
    """
    
    def __init__(self):
        """
        Initialize thread service with in-memory storage.
        """
        # In-memory storage for user threads
        self.user_threads = {}  # Maps user_id to thread_id
        self.active_threads = {}  # Simple thread storage (thread_id -> thread_data)
        logger.info("ThreadService initialized")
    
    def get_or_create_user_thread(self, user_id: str) -> str:
        """
        Get existing thread for user or create a new one.
        
        Args:
            user_id: User identifier
            
        Returns:
            str: Thread identifier
        """
        if user_id in self.user_threads:
            thread_id = self.user_threads[user_id]
            # Check if thread exists in our active_threads
            if thread_id in self.active_threads:
                return thread_id
        
        # Create new thread with a UUID
        thread_id = str(uuid.uuid4())
        self.user_threads[user_id] = thread_id
        
        # Current timestamp
        now = datetime.now()
        
        # Create thread in memory
        self.active_threads[thread_id] = {
            "id": thread_id,
            "user_id": user_id,
            "title": f"{user_id}'s Thread",
            "created_at": now,
            "updated_at": now,
            "messages": []
        }
        logger.info(f"Created new thread {thread_id} for user {user_id}")
        return thread_id
    
    def get_thread(self, thread_id: str) -> Optional[ChatThread]:
        """
        Get a thread by ID.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            Optional[ChatThread]: The thread if found, None otherwise
        """
        if thread_id not in self.active_threads:
            return None
        
        thread_data = self.active_threads[thread_id]
        return ChatThread(
            id=thread_data["id"],
            user_id=thread_data["user_id"],
            title=thread_data["title"],
            created_at=thread_data["created_at"],
            updated_at=thread_data["updated_at"],
            messages=thread_data.get("messages", [])
        )
    
    def create_thread(self, request: CreateThreadRequest) -> ChatThread:
        """
        Create a new thread or return the existing one for the user.
        
        Args:
            request: Thread creation request
            
        Returns:
            ChatThread: The thread
        """
        # Check if user already has a thread
        if request.user_id in self.user_threads:
            thread_id = self.user_threads[request.user_id]
            # If thread exists, return it
            if thread_id in self.active_threads:
                return self.get_thread(thread_id)
        
        # Create new thread
        thread_id = str(uuid.uuid4())
        self.user_threads[request.user_id] = thread_id
        
        # Current timestamp
        now = datetime.now()
        
        # Create thread in memory
        self.active_threads[thread_id] = {
            "id": thread_id,
            "user_id": request.user_id,
            "title": request.title,
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "metadata": request.metadata
        }
        
        thread = ChatThread(
            id=thread_id,
            user_id=request.user_id,
            title=request.title,
            created_at=now,
            updated_at=now,
            metadata=request.metadata,
            messages=[]
        )
        
        logger.info(f"Created new thread {thread_id} for user {request.user_id}")
        return thread
    
    def list_threads(self, user_id: str) -> ChatThreadList:
        """
        List threads for a user - will only return the single thread for the user.
        
        Args:
            user_id: User identifier
            
        Returns:
            ChatThreadList: List with the user's thread
        """
        threads = []
        
        # Check if user has a thread
        if user_id in self.user_threads:
            thread_id = self.user_threads[user_id]
            if thread_id in self.active_threads:
                thread_data = self.active_threads[thread_id]
                
                # Create thread summary
                message_count = len(thread_data.get("messages", []))
                last_message = None
                if message_count > 0:
                    last_message = thread_data["messages"][-1].content
                
                threads.append(ChatThreadSummary(
                    id=thread_id,
                    user_id=user_id,
                    title=thread_data["title"],
                    created_at=thread_data["created_at"],
                    updated_at=thread_data["updated_at"],
                    message_count=message_count,
                    last_message_preview=last_message[:50] + "..." if last_message and len(last_message) > 50 else last_message
                ))
        
        # Always return a list, even if empty
        return ChatThreadList(
            threads=threads,
            total=len(threads),
            has_more=False,
            page=1,
            page_size=20
        )
    
    def update_thread_title(self, thread_id: str, title: str) -> bool:
        """
        Update the title of a thread.
        
        Args:
            thread_id: Thread identifier
            title: New title
            
        Returns:
            bool: Success status
        """
        if thread_id not in self.active_threads:
            return False
        
        self.active_threads[thread_id]["title"] = title
        self.active_threads[thread_id]["updated_at"] = datetime.now()
        logger.info(f"Updated title for thread {thread_id}")
        return True
    
    def delete_thread(self, thread_id: str) -> bool:
        """
        Delete a thread.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            bool: Success status
        """
        if thread_id not in self.active_threads:
            return False
        
        # Get user ID to remove from user_threads mapping
        user_id = self.active_threads[thread_id]["user_id"]
        
        # Remove thread
        del self.active_threads[thread_id]
        
        # Remove from user mapping if it matches
        if user_id in self.user_threads and self.user_threads[user_id] == thread_id:
            del self.user_threads[user_id]
        
        logger.info(f"Deleted thread {thread_id}")
        return True
    
    def add_message_to_thread(self, thread_id: str, message):
        """
        Add a message to a thread's message list.
        
        Args:
            thread_id: Thread identifier
            message: Message to add
            
        Returns:
            bool: Success status
        """
        if thread_id not in self.active_threads:
            return False
        
        # Update the thread's message list and updated_at timestamp
        self.active_threads[thread_id]["messages"].append(message)
        self.active_threads[thread_id]["updated_at"] = datetime.now()
        
        return True
    
    def get_messages(self, thread_id: str, limit: int = 100):
        """
        Get messages from a thread.
        
        Args:
            thread_id: Thread identifier
            limit: Maximum number of messages to return
            
        Returns:
            List: Thread messages
        """
        if thread_id not in self.active_threads:
            return []
        
        messages = self.active_threads[thread_id].get("messages", [])
        # Return last 'limit' messages
        return messages[-limit:] if messages else []

# Singleton instance
thread_service = ThreadService()

def get_thread_service():
    return thread_service
