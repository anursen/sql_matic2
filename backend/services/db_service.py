import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

from backend.models.data_models import (
    ChatMessage, 
    ChatThread, 
    ChatThreadSummary, 
    ChatThreadList
)
from backend.utils.logger import get_logger
from backend.config.config import config

logger = get_logger(__name__)

class ChatDBService:
    """
    Database service for managing chat history including threads and messages.
    Handles all database operations related to chat storage.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database service with a connection to the SQLite database.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses path from config.
        """
        self.db_path = db_path or config.get('database', 'path', 'sql_matic_chat.db')
        logger.info(f"Initializing ChatDBService with database: {self.db_path}")
        self._initialize_db()
        
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        Ensures connections are properly closed after use.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _initialize_db(self):
        """
        Initialize the database by creating necessary tables if they don't exist.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create chat_threads table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_threads (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    metadata TEXT
                )
                """)
                
                # Create chat_messages table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    user_id TEXT,
                    metadata TEXT,
                    FOREIGN KEY (thread_id) REFERENCES chat_threads (id) ON DELETE CASCADE
                )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_id 
                ON chat_messages (thread_id)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_threads_user_id 
                ON chat_threads (user_id)
                """)
                
                conn.commit()
                logger.info("Chat database tables initialized successfully")
        except Exception as e:
            logger.error(f"Chat database initialization failed: {str(e)}")
            raise
    
    def create_thread(self, user_id: str, title: str, 
                      metadata: Optional[Dict[str, Any]] = None) -> ChatThread:
        """
        Create a new chat thread.
        
        Args:
            user_id: User identifier for the thread owner
            title: Title of the thread
            metadata: Optional additional metadata for the thread
            
        Returns:
            ChatThread: The created thread object
        """
        try:
            thread_id = str(uuid.uuid4())
            now = datetime.now()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO chat_threads (id, user_id, title, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        thread_id,
                        user_id,
                        title,
                        now,
                        now,
                        json.dumps(metadata) if metadata else None
                    )
                )
                conn.commit()
                
                logger.info(f"Created chat thread {thread_id} for user {user_id}")
                return ChatThread(
                    id=thread_id,
                    user_id=user_id,
                    title=title,
                    created_at=now,
                    updated_at=now,
                    metadata=metadata
                )
        except Exception as e:
            logger.error(f"Failed to create chat thread: {str(e)}")
            raise
    
    def get_thread(self, thread_id: str, with_messages: bool = False) -> Optional[ChatThread]:
        """
        Get a thread by its ID.
        
        Args:
            thread_id: The thread identifier
            with_messages: Whether to include thread messages
            
        Returns:
            ChatThread: The thread object if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chat_threads WHERE id = ?", (thread_id,))
                row = cursor.fetchone()
                
                if not row:
                    logger.info(f"Chat thread {thread_id} not found")
                    return None
                
                metadata = json.loads(row['metadata']) if row['metadata'] else None
                
                thread = ChatThread(
                    id=row['id'],
                    user_id=row['user_id'],
                    title=row['title'],
                    created_at=datetime.fromisoformat(str(row['created_at'])),
                    updated_at=datetime.fromisoformat(str(row['updated_at'])),
                    metadata=metadata
                )
                
                if with_messages:
                    thread.messages = self.get_messages(thread_id)
                
                return thread
        except Exception as e:
            logger.error(f"Failed to get chat thread {thread_id}: {str(e)}")
            raise
    
    def list_threads(self, user_id: str, page: int = 1, 
                     page_size: int = 20) -> ChatThreadList:
        """
        List threads for a specific user with pagination.
        
        Args:
            user_id: User identifier to filter threads
            page: Page number (starts from 1)
            page_size: Number of threads per page
            
        Returns:
            ChatThreadList: List of thread summaries with pagination info
        """
        try:
            offset = (page - 1) * page_size
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Count total threads for this user
                cursor.execute("SELECT COUNT(*) FROM chat_threads WHERE user_id = ?", (user_id,))
                total = cursor.fetchone()[0]
                
                # Get threads with pagination
                cursor.execute(
                    """
                    SELECT t.*, 
                           COUNT(m.id) as message_count,
                           (SELECT content FROM chat_messages 
                            WHERE thread_id = t.id 
                            ORDER BY created_at DESC LIMIT 1) as last_message
                    FROM chat_threads t
                    LEFT JOIN chat_messages m ON t.id = m.thread_id
                    WHERE t.user_id = ?
                    GROUP BY t.id
                    ORDER BY t.updated_at DESC
                    LIMIT ? OFFSET ?
                    """, 
                    (user_id, page_size, offset)
                )
                
                threads = []
                for row in cursor.fetchall():
                    metadata = json.loads(row['metadata']) if row['metadata'] else None
                    
                    # Create thread summary with message count and last message preview
                    last_message_preview = None
                    if row['last_message']:
                        last_message = row['last_message']
                        if len(last_message) > 50:
                            last_message_preview = last_message[:47] + "..."
                        else:
                            last_message_preview = last_message
                    
                    threads.append(ChatThreadSummary(
                        id=row['id'],
                        user_id=row['user_id'],
                        title=row['title'],
                        created_at=datetime.fromisoformat(str(row['created_at'])),
                        updated_at=datetime.fromisoformat(str(row['updated_at'])),
                        message_count=row['message_count'],
                        last_message_preview=last_message_preview
                    ))
                
                has_more = (offset + len(threads)) < total
                
                return ChatThreadList(
                    threads=threads,
                    total=total,
                    has_more=has_more,
                    page=page,
                    page_size=page_size
                )
        except Exception as e:
            logger.error(f"Failed to list chat threads for user {user_id}: {str(e)}")
            raise
    
    def add_message(self, thread_id: str, role: str, content: str,
                    user_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
        """
        Add a message to a thread.
        
        Args:
            thread_id: Thread identifier
            role: Role of the message sender (user/assistant/system)
            content: Content of the message
            user_id: Optional user identifier for user messages
            metadata: Optional additional metadata
            
        Returns:
            ChatMessage: The created message object
        """
        try:
            message_id = str(uuid.uuid4())
            now = datetime.now()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # First verify thread exists
                cursor.execute("SELECT id FROM chat_threads WHERE id = ?", (thread_id,))
                if not cursor.fetchone():
                    logger.error(f"Cannot add message to non-existent thread {thread_id}")
                    raise ValueError(f"Thread {thread_id} does not exist")
                
                # Add message
                cursor.execute(
                    """
                    INSERT INTO chat_messages (id, thread_id, role, content, created_at, user_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message_id,
                        thread_id,
                        role,
                        content,
                        now,
                        user_id,
                        json.dumps(metadata) if metadata else None
                    )
                )
                
                # Update thread's updated_at timestamp
                cursor.execute(
                    "UPDATE chat_threads SET updated_at = ? WHERE id = ?",
                    (now, thread_id)
                )
                
                conn.commit()
                
                logger.info(f"Added message {message_id} to thread {thread_id}")
                return ChatMessage(
                    id=message_id,
                    thread_id=thread_id,
                    role=role,
                    content=content,
                    created_at=now,
                    user_id=user_id,
                    metadata=metadata
                )
        except Exception as e:
            logger.error(f"Failed to add message to thread {thread_id}: {str(e)}")
            raise
    
    def get_messages(self, thread_id: str, limit: int = 100) -> List[ChatMessage]:
        """
        Get messages from a thread.
        
        Args:
            thread_id: Thread identifier
            limit: Maximum number of messages to return
            
        Returns:
            List[ChatMessage]: List of message objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM chat_messages 
                    WHERE thread_id = ? 
                    ORDER BY created_at ASC
                    LIMIT ?
                    """, 
                    (thread_id, limit)
                )
                
                messages = []
                for row in cursor.fetchall():
                    metadata = json.loads(row['metadata']) if row['metadata'] else None
                    messages.append(ChatMessage(
                        id=row['id'],
                        thread_id=row['thread_id'],
                        role=row['role'],
                        content=row['content'],
                        created_at=datetime.fromisoformat(str(row['created_at'])),
                        user_id=row['user_id'],
                        metadata=metadata
                    ))
                
                return messages
        except Exception as e:
            logger.error(f"Failed to get messages for thread {thread_id}: {str(e)}")
            raise
    
    def delete_thread(self, thread_id: str) -> bool:
        """
        Delete a thread and all its messages.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            bool: True if thread was deleted, False if thread wasn't found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if thread exists
                cursor.execute("SELECT id FROM chat_threads WHERE id = ?", (thread_id,))
                if not cursor.fetchone():
                    logger.info(f"Chat thread {thread_id} not found for deletion")
                    return False
                
                # Delete thread (cascade will delete messages)
                cursor.execute("DELETE FROM chat_threads WHERE id = ?", (thread_id,))
                conn.commit()
                
                logger.info(f"Deleted chat thread {thread_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete chat thread {thread_id}: {str(e)}")
            raise
    
    def update_thread_title(self, thread_id: str, title: str) -> bool:
        """
        Update the title of a thread.
        
        Args:
            thread_id: Thread identifier
            title: New title for the thread
            
        Returns:
            bool: True if thread was updated, False if thread wasn't found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if thread exists
                cursor.execute("SELECT id FROM chat_threads WHERE id = ?", (thread_id,))
                if not cursor.fetchone():
                    logger.info(f"Chat thread {thread_id} not found for updating title")
                    return False
                
                # Update thread title
                cursor.execute(
                    """
                    UPDATE chat_threads 
                    SET title = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (title, datetime.now(), thread_id)
                )
                conn.commit()
                
                logger.info(f"Updated title for chat thread {thread_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update title for chat thread {thread_id}: {str(e)}")
            raise
    
    def search_threads(self, user_id: str, query: str, 
                       page: int = 1, page_size: int = 20) -> ChatThreadList:
        """
        Search for threads by title or message content.
        
        Args:
            user_id: User identifier to filter threads
            query: Search query string
            page: Page number (starts from 1)
            page_size: Number of threads per page
            
        Returns:
            ChatThreadList: List of matching thread summaries
        """
        try:
            offset = (page - 1) * page_size
            search_term = f"%{query}%"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Count total matching threads
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT t.id) 
                    FROM chat_threads t
                    LEFT JOIN chat_messages m ON t.id = m.thread_id
                    WHERE t.user_id = ? 
                    AND (t.title LIKE ? OR m.content LIKE ?)
                    """, 
                    (user_id, search_term, search_term)
                )
                total = cursor.fetchone()[0]
                
                # Get matching threads with pagination
                cursor.execute(
                    """
                    SELECT t.*, 
                           COUNT(m2.id) as message_count,
                           (SELECT content FROM chat_messages 
                            WHERE thread_id = t.id 
                            ORDER BY created_at DESC LIMIT 1) as last_message
                    FROM chat_threads t
                    LEFT JOIN chat_messages m ON t.id = m.thread_id
                    LEFT JOIN chat_messages m2 ON t.id = m2.thread_id
                    WHERE t.user_id = ? 
                    AND (t.title LIKE ? OR m.content LIKE ?)
                    GROUP BY t.id
                    ORDER BY t.updated_at DESC
                    LIMIT ? OFFSET ?
                    """, 
                    (user_id, search_term, search_term, page_size, offset)
                )
                
                threads = []
                for row in cursor.fetchall():
                    metadata = json.loads(row['metadata']) if row['metadata'] else None
                    
                    # Create thread summary with message count and last message preview
                    last_message_preview = None
                    if row['last_message']:
                        last_message = row['last_message']
                        if len(last_message) > 50:
                            last_message_preview = last_message[:47] + "..."
                        else:
                            last_message_preview = last_message
                    
                    threads.append(ChatThreadSummary(
                        id=row['id'],
                        user_id=row['user_id'],
                        title=row['title'],
                        created_at=datetime.fromisoformat(str(row['created_at'])),
                        updated_at=datetime.fromisoformat(str(row['updated_at'])),
                        message_count=row['message_count'],
                        last_message_preview=last_message_preview
                    ))
                
                has_more = (offset + len(threads)) < total
                
                return ChatThreadList(
                    threads=threads,
                    total=total,
                    has_more=has_more,
                    page=page,
                    page_size=page_size
                )
        except Exception as e:
            logger.error(f"Failed to search threads for user {user_id}: {str(e)}")
            raise
