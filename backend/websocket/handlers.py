import json
import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from ..services.chat_service import ChatService
from ..models.data_models import AddMessageRequest

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self, chat_service: ChatService):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_info: Dict[str, Dict[str, Any]] = {}
        self.chat_service = chat_service
    
    async def connect(self, websocket: WebSocket, client_id: str, 
                      user_id: Optional[str] = None, thread_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Store client info
        self.client_info[client_id] = {
            "user_id": user_id or "anonymous",
            "thread_id": thread_id
        }
        
        # If user_id provided but no thread_id, get or create a thread
        if user_id and not thread_id:
            thread_id = await self.chat_service.get_or_create_user_thread(user_id)
            self.client_info[client_id]["thread_id"] = thread_id
            
            # Send thread_id back to the client
            await self.send_message(client_id, {
                "type": "thread_info",
                "payload": {
                    "thread_id": thread_id,
                    "user_id": user_id
                }
            })
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_info:
            del self.client_info[client_id]
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[str] = None):
        for client_id, connection in self.active_connections.items():
            if client_id != exclude:
                await connection.send_json(message)
    
    async def handle_chat_message(self, client_id: str, data: Dict[str, Any]):
        # Extract message data
        message = data.get("message", "")
        user_id = data.get("user_id") or self.client_info[client_id].get("user_id")
        thread_id = data.get("thread_id") or self.client_info[client_id].get("thread_id")
        
        # If no thread_id yet, get or create one
        if not thread_id and user_id:
            thread_id = await self.chat_service.get_or_create_user_thread(user_id)
            self.client_info[client_id]["thread_id"] = thread_id
        
        # Add message to thread
        user_msg_request = AddMessageRequest(
            thread_id=thread_id,
            role="user",
            content=message,
            user_id=user_id
        )
        await self.chat_service.add_message(user_msg_request)
        
        # Process message (in a real app, this would call the AI agent)
        # This is a simple echo response for now
        response = f"Echo: {message}"
        
        # Send typing indicator
        await self.send_message(client_id, {
            "type": "typing_indicator",
            "payload": {
                "isTyping": True
            }
        })
        
        # Add response to thread
        assistant_msg_request = AddMessageRequest(
            thread_id=thread_id,
            role="assistant",
            content=response,
            user_id="assistant"
        )
        response_obj = await self.chat_service.add_message(assistant_msg_request)
        
        # Send response
        await self.send_message(client_id, {
            "type": "chat_message",
            "payload": {
                "message": {
                    "role": "assistant",
                    "content": response,
                    "created_at": response_obj.created_at.isoformat()
                },
                "thread_id": thread_id
            }
        })
        
        # Clear typing indicator
        await self.send_message(client_id, {
            "type": "typing_indicator",
            "payload": {
                "isTyping": False
            }
        })

websocket_manager = None

def get_websocket_manager(chat_service: ChatService) -> WebSocketManager:
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = WebSocketManager(chat_service)
    return websocket_manager
