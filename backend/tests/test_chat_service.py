import asyncio
import pytest
import os
import tempfile

from backend.services.db_service import ChatDBService
from backend.services.chat_service import ChatService
from backend.models.data_models import CreateThreadRequest, AddMessageRequest

@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def chat_service(temp_db):
    """Create a chat service instance with a temporary database."""
    db_service = ChatDBService(db_path=temp_db)
    return ChatService(db_service=db_service)

@pytest.mark.asyncio
async def test_create_thread(chat_service):
    """Test creating a new chat thread."""
    request = CreateThreadRequest(
        user_id="test_user",
        title="Test Thread",
        system_message="This is a system message"
    )
    
    thread = await chat_service.create_thread(request)
    
    assert thread is not None
    assert thread.id is not None
    assert thread.user_id == "test_user"
    assert thread.title == "Test Thread"
    
    # Get the thread to verify system message
    saved_thread = await chat_service.get_thread(thread.id)
    assert saved_thread is not None
    
    # There should be one system message
    messages = await chat_service.get_messages(thread.id)
    assert len(messages) == 1
    assert messages[0].role == "system"
    assert messages[0].content == "This is a system message"

@pytest.mark.asyncio
async def test_add_message(chat_service):
    """Test adding messages to a thread."""
    # Create a thread first
    request = CreateThreadRequest(
        user_id="test_user",
        title="Test Thread for Messages"
    )
    
    thread = await chat_service.create_thread(request)
    
    # Add a user message
    user_msg_request = AddMessageRequest(
        thread_id=thread.id,
        role="user",
        content="Hello, this is a test message",
        user_id="test_user"
    )
    
    user_message = await chat_service.add_message(user_msg_request)
    assert user_message is not None
    assert user_message.role == "user"
    assert user_message.content == "Hello, this is a test message"
    
    # Add an assistant message
    assistant_msg_request = AddMessageRequest(
        thread_id=thread.id,
        role="assistant",
        content="I'm an AI assistant, how can I help?"
    )
    
    assistant_message = await chat_service.add_message(assistant_msg_request)
    assert assistant_message is not None
    assert assistant_message.role == "assistant"
    
    # Get all messages
    messages = await chat_service.get_messages(thread.id)
    assert len(messages) == 2  # User and assistant messages

@pytest.mark.asyncio
async def test_list_threads(chat_service):
    """Test listing threads for a user."""
    # Create multiple threads
    for i in range(5):
        request = CreateThreadRequest(
            user_id="test_user",
            title=f"Test Thread {i}"
        )
        await chat_service.create_thread(request)
    
    # List threads
    thread_list = await chat_service.list_threads("test_user")
    
    assert thread_list is not None
    assert thread_list.total == 5
    assert len(thread_list.threads) == 5

@pytest.mark.asyncio
async def test_search_threads(chat_service):
    """Test searching for threads."""
    # Create threads with different titles
    request1 = CreateThreadRequest(
        user_id="test_user",
        title="SQL Query Help"
    )
    thread1 = await chat_service.create_thread(request1)
    
    request2 = CreateThreadRequest(
        user_id="test_user",
        title="Python Programming"
    )
    thread2 = await chat_service.create_thread(request2)
    
    # Add messages to threads
    await chat_service.add_message(AddMessageRequest(
        thread_id=thread1.id,
        role="user",
        content="How do I join tables in SQL?",
        user_id="test_user"
    ))
    
    await chat_service.add_message(AddMessageRequest(
        thread_id=thread2.id,
        role="user",
        content="How do I use async/await in Python?",
        user_id="test_user"
    ))
    
    # Search for SQL-related threads
    sql_results = await chat_service.search_threads("test_user", "SQL")
    assert sql_results.total == 1
    assert sql_results.threads[0].title == "SQL Query Help"
    
    # Search for Python-related threads
    python_results = await chat_service.search_threads("test_user", "Python")
    assert python_results.total == 1
    assert python_results.threads[0].title == "Python Programming"
    
    # Search for content
    join_results = await chat_service.search_threads("test_user", "join tables")
    assert join_results.total == 1

if __name__ == "__main__":
    asyncio.run(pytest.main(["-xvs", "test_chat_service.py"]))
