import os
import sys
from typing import List, Dict

# Add the parent directory to sys.path to make backend package importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.services.agent_service import agent_service
from backend.utils import logger
from backend.api import router as api_router
from backend.config.config import config

# Initialize FastAPI app
app = FastAPI(title="SQL Matic API")

# Add CORS middleware
origins = ["*"]  # Update with your frontend URL in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Add a health check endpoint for testing
@app.get("/health")
async def health_check():
    """Health check endpoint for testing the API is running"""
    return {
        "status": "ok",
        "version": "1.0",
        "database": config.get("query_db", "path", "not configured")
    }

# Add a tools check endpoint to verify loaded tools
@app.get("/tools")
async def list_tools():
    """List all loaded tools in the active agent"""
    if not agent_service.active_agent:
        return {"count": 0, "tools": []}
    
    tools = [tool.name for tool in agent_service.active_agent.tools]
    return {
        "count": len(tools),
        "tools": tools
    }

# Add an agent info endpoint
@app.get("/agent")
async def get_agent_info():
    """Get information about the active agent"""
    if not agent_service.active_agent:
        return {"status": "no_agent"}
    
    agent = agent_service.active_agent
    return {
        "status": "active",
        "name": agent.name,
        "description": agent.description,
        "tool_count": len(agent.tools),
        "tools": [tool.name for tool in agent.tools]
    }

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
            message = {
                "type": event_type,
                "data": data
            }
            for connection in self.active_connections[thread_id]:
                await connection.send_json(message)

# Create connection manager instance
connection_manager = ConnectionManager()

@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await connection_manager.connect(websocket, thread_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data["type"] == "chat_message":
                # Process the message using the agent
                user_message = data["data"]["message"]
                user_id = data["data"]["user_id"]
                system_message = data["data"].get("system_message")
                
                # Send typing indicator
                await connection_manager.broadcast(
                    thread_id, 
                    "typing_indicator", 
                    {"isTyping": True}
                )
                
                # Stream the response
                for event_type, event_data in agent_service.stream_message(
                    message_text=user_message,
                    thread_id=thread_id,
                    user_id=user_id,
                    system_message=system_message
                ):
                    await connection_manager.broadcast(thread_id, event_type, event_data)
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, thread_id)

if __name__ == "__main__":
    # Get port from environment variables or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)

