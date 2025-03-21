import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models.data_models import (
    Message, Thread, ChatRequest, ChatResponse, 
    CreateThreadRequest, DatabaseStructure, Metrics
)
from services.agent_service import sql_agent
from services.thread_service import thread_service
from services.db_service import db_service
from backend.utils import logger  # Import the logger directly
from backend.config.config import config

# Initialize FastAPI app
app = FastAPI(title="SQL Matic API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get_section("cors").get("origins", ["*"]),
    allow_credentials=config.get("cors", "credentials", True),
    allow_methods=config.get_section("cors").get("methods", ["*"]),
    allow_headers=config.get_section("cors").get("headers", ["*"]),
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, thread_id: str):
        await websocket.accept()
        if thread_id not in self.active_connections:
            self.active_connections[thread_id] = []
        self.active_connections[thread_id].append(websocket)
        logger.info(f"Client connected to thread {thread_id}. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, thread_id: str):
        if thread_id in self.active_connections:
            if websocket in self.active_connections[thread_id]:
                self.active_connections[thread_id].remove(websocket)
            if not self.active_connections[thread_id]:
                del self.active_connections[thread_id]
        logger.info(f"Client disconnected from thread {thread_id}. Active connections: {len(self.active_connections)}")

    async def broadcast(self, thread_id: str, event_type: str, data: dict):
        if thread_id in self.active_connections:
            for connection in self.active_connections[thread_id]:
                await connection.send_json({
                    "type": event_type,
                    "data": data
                })
            logger.info(f"Broadcast {event_type} to {len(self.active_connections[thread_id])} clients in thread {thread_id}")

manager = ConnectionManager()

# API Routes

@app.get("/")
async def root():
    return {"message": "SQL Matic API is running"}

@app.post("/api/chat", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """Send a chat message and get a response"""
    try:
        # Create user message
        user_message = Message(
            text=request.message,
            sender="user",
            userId=request.userId,
            timestamp=datetime.now().isoformat(),
            threadId=request.threadId
        )
        
        # Add to thread
        thread_service.add_message(request.threadId, user_message)
        
        # Get response from agent
        response = sql_agent.send_message(
            message_text=request.message,
            thread_id=request.threadId,
            user_id=request.userId
        )
        
        # Create bot message
        bot_message = Message(
            text=response.text,
            sender="bot",
            userId="SQL-Bot",
            timestamp=response.timestamp,
            threadId=request.threadId
        )
        
        # Add to thread
        thread_service.add_message(request.threadId, bot_message)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threads", response_model=Dict[str, List[Thread]])
async def get_threads():
    """Get all chat threads"""
    try:
        threads = thread_service.get_all_threads()
        return {"threads": threads}
    except Exception as e:
        logger.error(f"Error getting threads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threads/{thread_id}/messages", response_model=Dict[str, List[Message]])
async def get_thread_messages(thread_id: str):
    """Get messages for a specific thread"""
    try:
        messages = thread_service.get_messages(thread_id)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/threads", response_model=Thread)
async def create_thread(request: CreateThreadRequest):
    """Create a new thread"""
    try:
        thread = thread_service.create_thread(
            name=request.name,
            user_id=request.userId
        )
        return thread
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/structure", response_model=DatabaseStructure)
async def get_database_structure():
    """Get the database structure"""
    try:
        return db_service.get_structure()
    except Exception as e:
        logger.error(f"Error getting database structure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics", response_model=Metrics)
async def get_metrics():
    """Get usage metrics"""
    try:
        return sql_agent.metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, thread_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            request = json.loads(data)
            
            # Process the message
            if "message" in request and "userId" in request:
                user_message = Message(
                    text=request["message"],
                    sender="user",
                    userId=request["userId"],
                    timestamp=datetime.now().isoformat(),
                    threadId=thread_id
                )
                
                # Add to thread
                thread_service.add_message(thread_id, user_message)
                
                # Broadcast user message to all connected clients
                await manager.broadcast(
                    thread_id=thread_id,
                    event_type="message",
                    data=user_message.dict()
                )
                
                # Stream response from agent
                for event_type, event_data in sql_agent.stream_message(
                    message_text=request["message"],
                    thread_id=thread_id,
                    user_id=request["userId"]
                ):
                    # Broadcast each chunk to all connected clients
                    await manager.broadcast(
                        thread_id=thread_id,
                        event_type=event_type,
                        data=event_data
                    )
                    
                    # If it's a message, add it to the thread
                    if event_type == "message":
                        bot_message = Message(
                            text=event_data["text"],
                            sender="bot",
                            userId="SQL-Bot",
                            timestamp=datetime.now().isoformat(),
                            threadId=thread_id
                        )
                        thread_service.add_message(thread_id, bot_message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, thread_id)
    except Exception as e:
        logger.exception(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket, thread_id)


if __name__ == "__main__":
    # Get port from config or environment
    port = int(os.environ.get("PORT", config.get("app", "port", 8000)))
    
    # Log server startup
    logger.info(f"Starting SQL Matic API server on port {port}")
    
    # Run the app with uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
    
    