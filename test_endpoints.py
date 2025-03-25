import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_thread():
    """Test creating a new chat thread."""
    url = f"{BASE_URL}/chat/threads"
    data = {
        "user_id": "test_user",
        "title": "Python Help Thread",
        "system_message": "You are a helpful Python assistant."
    }
    response = requests.post(url, json=data)
    print("Create Thread Response:", response.status_code)
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_add_message(thread_id):
    """Test adding a message to a thread."""
    url = f"{BASE_URL}/chat/messages"
    data = {
        "thread_id": thread_id,
        "role": "user",
        "content": "How do I use async/await in Python?",
        "user_id": "test_user"
    }
    response = requests.post(url, json=data)
    print("Add Message Response:", response.status_code)
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_list_threads():
    """Test listing threads for a user."""
    url = f"{BASE_URL}/chat/threads?user_id=test_user"
    response = requests.get(url)
    print("List Threads Response:", response.status_code)
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_get_thread(thread_id):
    """Test getting a thread by ID."""
    url = f"{BASE_URL}/chat/threads/{thread_id}"
    response = requests.get(url)
    print("Get Thread Response:", response.status_code)
    print(json.dumps(response.json(), indent=2))
    return response.json()

def run_tests():
    # Create a thread and get its ID
    thread = test_create_thread()
    thread_id = thread["id"]
    
    # Add a message to the thread
    test_add_message(thread_id)
    
    # List all threads
    test_list_threads()
    
    # Get the thread with messages
    test_get_thread(thread_id)

if __name__ == "__main__":
    run_tests()
