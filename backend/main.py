import os
import sys
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to sys.path to make backend package importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uvicorn
from backend.services.agent_service import agent_service
from backend.utils import logger
from backend.api import router as api_router
from backend.config.config import config
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SQL Matic API",
    description="Backend API for SQL Matic application",
    version="1.0.0"
)

# Configure CORS
origins = config.get_section("cors").get("origins", ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint that returns service info."""
    return {"message": "SQL Matic API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

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
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_json(self, client_id: str, data: Any):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    logger.info("connection open")
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Extract message details
            message_type = message_data.get("type")
            payload = message_data.get("payload", {})
            
            if message_type == "chat_message":
                # The structure seems to be different from what we expected
                # Check both direct message and nested data structure
                if "message" in payload:
                    user_message = payload.get("message", "")
                elif "data" in message_data and "message" in message_data["data"]:
                    user_message = message_data["data"]["message"]
                else:
                    user_message = ""
                
                thread_id = payload.get("thread_id", "")
                user_id = payload.get("user_id", "")
                agent_id = payload.get("agent_id")  # Optional agent ID
                
                # Validate message is not empty
                if not user_message or user_message.strip() == "":
                    logger.warning(f"Empty message received from client {client_id}")
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Please provide a message. Empty messages cannot be processed."}
                    })
                    continue
                
                logger.info(f"Processing message from {user_id}: '{user_message[:50]}...'") if len(user_message) > 50 else logger.info(f"Processing message from {user_id}: '{user_message}'")
                
                # Stream the response
                for event_type, event_data in agent_service.stream_message(
                    message_text=user_message,
                    thread_id=thread_id,
                    user_id=user_id,
                    agent_id=agent_id
                ):
                    await websocket.send_json({
                        "type": event_type,
                        "payload": event_data
                    })
            
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "payload": {"message": f"Error: {str(e)}"}
            })
        except:
            pass
        manager.disconnect(client_id)

if __name__ == "__main__":
    port = config.get("app", "port", 8000)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

