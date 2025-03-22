import time
import uuid
from typing import Dict, List, Optional

from backend.models.data_models import Thread, Message
from backend.utils import logger


class ThreadService:
    """Service to manage conversation threads"""
    
    def __init__(self):
        # Simple in-memory storage for threads
        self.threads: Dict[str, Thread] = {}
    
    def create_thread(self, user_id: str) -> Thread:
        """Create a new thread"""
        thread_id = str(uuid.uuid4())
        thread = Thread(
            id=thread_id,
            user_id=user_id,
            messages=[],
            created_at=time.time(),
            updated_at=time.time()
        )
        self.threads[thread_id] = thread
        logger.info(f"Created new thread {thread_id} for user {user_id}")
        return thread
    
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID"""
        return self.threads.get(thread_id)
    
    def get_threads(self, user_id: Optional[str] = None) -> List[Thread]:
        """Get all threads, optionally filtered by user_id"""
        if user_id:
            return [thread for thread in self.threads.values() if thread.user_id == user_id]
        return list(self.threads.values())
    
    def add_message(self, thread_id: str, message: Message) -> bool:
        """Add a message to a thread"""
        if thread_id not in self.threads:
            return False
        
        thread = self.threads[thread_id]
        thread.messages.append(message)
        thread.updated_at = time.time()
        return True
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread by ID"""
        if thread_id in self.threads:
            del self.threads[thread_id]
            logger.info(f"Deleted thread {thread_id}")
            return True
        return False

# Create a singleton instance
thread_service = ThreadService()
