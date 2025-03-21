import time
from typing import Dict, List, Optional
from datetime import datetime

from backend.models.data_models import Thread, Message


class ThreadService:
    """Service to manage chat threads"""
    
    def __init__(self):
        self.threads: Dict[str, Thread] = {}
        
        # Create a default thread if none exists
        default_thread = Thread(
            id="default",
            name="New Conversation",
            lastMessageTime=datetime.now().isoformat()
        )
        
        # Add welcome message
        welcome_message = Message(
            text="# Welcome to SQL Matic! 👋\n\nI'm your SQL assistant. You can ask me questions about SQL queries, database design, or specific SQL commands.",
            sender="bot",
            userId="SQL-Bot",
            timestamp=datetime.now().isoformat(),
            threadId="default"
        )
        
        default_thread.messages.append(welcome_message)
        self.threads["default"] = default_thread
    
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID"""
        return self.threads.get(thread_id)
    
    def get_all_threads(self) -> List[Thread]:
        """Get all threads"""
        return list(self.threads.values())
    
    def create_thread(self, name: str, user_id: str) -> Thread:
        """Create a new thread"""
        thread_id = f"thread-{int(time.time() * 1000)}"
        
        thread = Thread(
            id=thread_id,
            name=name,
            lastMessageTime=datetime.now().isoformat()
        )
        
        # Add welcome message
        welcome_message = Message(
            text="# New Thread Started\n\nHow can I help you with SQL today?",
            sender="bot",
            userId="SQL-Bot",
            timestamp=datetime.now().isoformat(),
            threadId=thread_id
        )
        
        thread.messages.append(welcome_message)
        self.threads[thread_id] = thread
        
        return thread
    
    def add_message(self, thread_id: str, message: Message) -> None:
        """Add a message to a thread"""
        thread = self.get_thread(thread_id)
        
        if thread:
            thread.messages.append(message)
            thread.lastMessageTime = message.timestamp
            
            # If it's the first user message, use it to name the thread
            if message.sender == "user" and len(thread.messages) <= 2:
                # Extract first line as title (max 30 chars)
                first_line = message.text.split('\n')[0][:30]
                thread.name = first_line
    
    def get_messages(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread"""
        thread = self.get_thread(thread_id)
        
        if thread:
            return thread.messages
        
        return []


# Create a singleton instance
thread_service = ThreadService()
