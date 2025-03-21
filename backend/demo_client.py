import asyncio
import json
import websockets
import requests
import time
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def chat_with_agent():
    """Simple terminal client to interact with the SQL agent"""
    print("\n=== SQL Matic Terminal Client ===")
    print("Type 'exit' to quit, 'new' to start a new thread\n")
    
    # Default user
    user_id = "User1"
    
    # Get available threads
    response = requests.get(f"{BASE_URL}/api/threads")
    threads = response.json()["threads"]
    
    if not threads:
        # Create a default thread
        response = requests.post(
            f"{BASE_URL}/api/threads",
            json={"name": "New Conversation", "userId": user_id}
        )
        thread_id = response.json()["id"]
        print(f"Created new thread: {thread_id}\n")
    else:
        # List available threads
        print("Available threads:")
        for i, thread in enumerate(threads):
            print(f"{i+1}. {thread['name']} (ID: {thread['id']})")
        
        # Let user select a thread
        selection = input("\nSelect a thread number or type 'new': ")
        
        if selection.lower() == "new":
            response = requests.post(
                f"{BASE_URL}/api/threads",
                json={"name": "New Conversation", "userId": user_id}
            )
            thread_id = response.json()["id"]
            print(f"Created new thread: {thread_id}\n")
        else:
            try:
                thread_index = int(selection) - 1
                thread_id = threads[thread_index]["id"]
                print(f"Selected thread: {thread_id}\n")
            except (ValueError, IndexError):
                print("Invalid selection. Using first thread.")
                thread_id = threads[0]["id"]
    
    # Connect to WebSocket
    async with websockets.connect(f"{WS_URL}/ws/{thread_id}") as websocket:
        # Display existing messages
        response = requests.get(f"{BASE_URL}/api/threads/{thread_id}/messages")
        messages = response.json()["messages"]
        
        for msg in messages:
            sender = "You" if msg["sender"] == "user" else "SQL-Bot"
            timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
            print(f"[{timestamp}] {sender}: {msg['text']}")
        
        # Start message loop
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            if user_input.lower() == "exit":
                break
            
            if user_input.lower() == "new":
                response = requests.post(
                    f"{BASE_URL}/api/threads",
                    json={"name": "New Conversation", "userId": user_id}
                )
                new_thread_id = response.json()["id"]
                print(f"\nCreated new thread: {new_thread_id}")
                print("Please restart the client to use the new thread")
                break
            
            # Send message to WebSocket
            await websocket.send(json.dumps({
                "message": user_input,
                "userId": user_id
            }))
            
            # Print "typing" indicator
            print("SQL-Bot is typing...", end="", flush=True)
            
            # Process responses
            bot_response = ""
            is_typing = True
            
            while is_typing:
                # Receive WebSocket message
                response = await websocket.recv()
                event = json.loads(response)
                
                # Handle different event types
                if event["type"] == "typing":
                    is_typing = event["data"]["isTyping"]
                    if not is_typing:
                        # Clear typing indicator
                        print("\r" + " " * 20 + "\r", end="", flush=True)
                
                elif event["type"] == "message":
                    # Clear typing indicator
                    print("\r" + " " * 20 + "\r", end="", flush=True)
                    # Print bot message
                    bot_response = event["data"]["text"]
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] SQL-Bot: {bot_response}")

if __name__ == "__main__":
    asyncio.run(chat_with_agent())
