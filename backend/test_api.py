import requests
import uuid
from pprint import pprint
import json
import sseclient  # You may need to install this: pip install sseclient-py

# Set the API base URL - adjust port if needed
BASE_URL = "http://localhost:8000"

def test_chat_endpoint():
    """Test the basic chat endpoint"""
    print("\n=== Testing Chat Endpoint ===")
    
    # Generate a unique thread ID
    thread_id = str(uuid.uuid4())
    user_id = "api_test_user"
    
    # Prepare the request payload
    payload = {
        "message": "What tables are in the database?",
        "thread_id": thread_id,
        "user_id": user_id
    }
    
    # Send the request
    print(f"Sending message: '{payload['message']}'")
    response = requests.post(f"{BASE_URL}/api/chat", json=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        print(f"Response received:")
        print(f"Response text: {data['text']}")
        print("\nThread ID:", data['thread_id'])
        
        # Send a follow-up message using the same thread_id
        payload = {
            "message": "Show me the structure of the users table",
            "thread_id": thread_id,
            "user_id": user_id
        }
        
        print(f"\nSending follow-up message: '{payload['message']}'")
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response received:")
            print(f"Response text: {data['text']}")
        else:
            print(f"Error with follow-up message: {response.status_code}")
            print(response.text)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_stream_chat_endpoint():
    """Test the streaming chat endpoint"""
    print("\n=== Testing Stream Chat Endpoint ===")
    
    # Generate a unique thread ID
    thread_id = str(uuid.uuid4())
    user_id = "api_test_user"
    
    # Prepare the request payload
    payload = {
        "message": "Write a SQL query to find all users who registered in the last month",
        "thread_id": thread_id,
        "user_id": user_id
    }
    
    # Send the request with stream=True
    print(f"Streaming message: '{payload['message']}'")
    response = requests.post(f"{BASE_URL}/api/chat/stream", json=payload, stream=True)
    
    # Process the server-sent events
    client = sseclient.SSEClient(response)
    
    print("\nReceiving events:")
    for event in client.events():
        data = json.loads(event.data)
        if "text" in data:
            print(f"  Message chunk: {data['text'][:50]}..." if len(data['text']) > 50 else f"  Message chunk: {data['text']}")
        elif "isTyping" in data:
            print(f"  Typing indicator: {data['isTyping']}")
        elif "metrics" in data:
            print("  Metrics received")
        elif "done" in data and data["done"]:
            print(f"  Stream completed, thread_id: {data['thread_id']}")

def test_get_threads_endpoint():
    """Test the get threads endpoint"""
    print("\n=== Testing Get Threads Endpoint ===")
    
    # Get all threads
    response = requests.get(f"{BASE_URL}/api/threads")
    
    if response.status_code == 200:
        threads = response.json()
        print(f"Retrieved {len(threads)} threads")
        
        if threads:
            # Get the first thread ID
            thread_id = threads[0]["id"]
            
            # Get a specific thread
            response = requests.get(f"{BASE_URL}/api/threads/{thread_id}")
            
            if response.status_code == 200:
                thread = response.json()
                print(f"\nRetrieved thread {thread_id}:")
                print(f"  User ID: {thread['user_id']}")
                print(f"  Message count: {len(thread['messages'])}")
                
                # Print the first few messages
                for i, msg in enumerate(thread['messages'][:3]):
                    print(f"  Message {i+1}: [{msg['sender']}] {msg['text'][:50]}..." if len(msg['text']) > 50 else f"  Message {i+1}: [{msg['sender']}] {msg['text']}")
            else:
                print(f"Error getting thread: {response.status_code}")
                print(response.text)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("SQL Agent API Test")
    print("=================")
    
    # Uncomment the tests you want to run
    test_chat_endpoint()
    test_stream_chat_endpoint()
    test_get_threads_endpoint()
