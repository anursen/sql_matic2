import os
import uuid
import dotenv
import time
from pprint import pprint

# Load environment variables from .env file
dotenv.load_dotenv()

def test_basic_message():
    """Test sending a basic message to the agent"""
    print("\n=== Testing Basic Message ===")
    
    # Import the agent singleton here to avoid circular imports
    from backend.services.agent_service import sql_agent
    
    # Generate a unique thread ID and user ID for this test
    thread_id = str(uuid.uuid4())
    user_id = "test_user_1"
    
    # Send a message to the agent
    message = "What tables are available in the database?"
    print(f"Sending message: '{message}'")
    
    # Measure response time
    start_time = time.time()
    response = sql_agent.send_message(message, thread_id, user_id)
    elapsed_time = time.time() - start_time
    
    print(f"Response received in {elapsed_time:.2f} seconds:")
    print(f"Response text: {response.text}")
    print("\nThread:")
    thread = sql_agent.get_thread(thread_id)
    for msg in thread.messages:
        print(f"- [{msg.sender}]: {msg.text[:100]}..." if len(msg.text) > 100 else f"- [{msg.sender}]: {msg.text}")
    
    print("\nMetrics:")
    pprint(response.metrics.dict())
    
    return thread_id, user_id

def test_follow_up_message(thread_id, user_id):
    """Test sending a follow-up message in the same thread"""
    print("\n=== Testing Follow-up Message ===")
    
    # Import the agent singleton here to avoid circular imports
    from backend.services.agent_service import sql_agent
    
    # Send a follow-up message that references the previous conversation
    message = "Can you show me the structure of the users table?"
    print(f"Sending follow-up message: '{message}'")
    
    # Measure response time
    start_time = time.time()
    response = sql_agent.send_message(message, thread_id, user_id)
    elapsed_time = time.time() - start_time
    
    print(f"Response received in {elapsed_time:.2f} seconds:")
    print(f"Response text: {response.text}")
    print("\nThread:")
    thread = sql_agent.get_thread(thread_id)
    for msg in thread.messages:
        print(f"- [{msg.sender}]: {msg.text[:100]}..." if len(msg.text) > 100 else f"- [{msg.sender}]: {msg.text}")
    
    print("\nMetrics:")
    pprint(response.metrics.dict())

def test_streaming_message():
    """Test streaming a message from the agent"""
    print("\n=== Testing Streaming Message ===")
    
    # Import the agent singleton here to avoid circular imports
    from backend.services.agent_service import sql_agent
    
    # Generate a unique thread ID and user ID for this test
    thread_id = str(uuid.uuid4())
    user_id = "test_user_2"
    
    # Send a message to the agent with streaming
    message = "Write a SQL query to find all users who registered in the last month"
    print(f"Streaming message: '{message}'")
    
    # Stream the response
    print("\nResponse stream:")
    for event_type, data in sql_agent.stream_message(message, thread_id, user_id):
        if event_type == "message":
            print(f"  Message chunk: {data['text'][:50]}..." if len(data['text']) > 50 else f"  Message chunk: {data['text']}")
        elif event_type == "typing":
            print(f"  Typing indicator: {data['isTyping']}")
        elif event_type == "metrics_update":
            print("  Metrics updated")
    
    # Get the final thread
    print("\nFinal Thread:")
    thread = sql_agent.get_thread(thread_id)
    for msg in thread.messages:
        print(f"- [{msg.sender}]: {msg.text[:100]}..." if len(msg.text) > 100 else f"- [{msg.sender}]: {msg.text}")

def test_thread_management():
    """Test thread management functionality"""
    print("\n=== Testing Thread Management ===")
    
    # Import the agent singleton here to avoid circular imports
    from backend.services.agent_service import sql_agent
    
    # Create some test threads
    threads = []
    for i in range(3):
        thread_id = str(uuid.uuid4())
        user_id = f"test_user_{i+1}"
        message = f"This is test message {i+1}"
        sql_agent.send_message(message, thread_id, user_id)
        threads.append((thread_id, user_id))
    
    # List all threads
    all_threads = sql_agent.get_threads()
    print(f"Total threads: {len(all_threads)}")
    
    # Get threads for a specific user
    user_threads = sql_agent.get_threads(threads[0][1])
    print(f"Threads for user {threads[0][1]}: {len(user_threads)}")
    
    # Delete a thread
    thread_to_delete = threads[0][0]
    success = sql_agent.delete_thread(thread_to_delete)
    print(f"Deleted thread {thread_to_delete}: {success}")
    
    # Verify thread was deleted
    remaining_threads = sql_agent.get_threads()
    print(f"Remaining threads: {len(remaining_threads)}")
    
    # Try to get the deleted thread
    deleted_thread = sql_agent.get_thread(thread_to_delete)
    print(f"Accessing deleted thread returns: {deleted_thread}")

if __name__ == "__main__":
    print("SQL Agent Test")
    print("==============")
    
    # Import the agent singleton
    from backend.services.agent_service import sql_agent
    
    # Test sending a basic message
    thread_id, user_id = test_basic_message()
    
    # Test sending a follow-up message
    test_follow_up_message(thread_id, user_id)
    
    # Test streaming a message
    test_streaming_message()
    
    # Test thread management
    test_thread_management()
