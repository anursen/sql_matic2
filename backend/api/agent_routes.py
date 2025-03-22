import uuid
import json
import asyncio
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.services.agent_service import agent_service
from backend.models.data_models import ChatRequest, ChatResponse, Thread

router = APIRouter()

class AgentInfo(BaseModel):
    id: str
    name: str
    description: str

class SystemMessageRequest(BaseModel):
    thread_id: Optional[str] = None
    user_id: str
    system_message: str
    message: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return the response"""
    # Generate a thread_id if not provided
    thread_id = request.thread_id or str(uuid.uuid4())
    
    # Send the message to the agent
    response = agent_service.send_message(
        message_text=request.message,
        thread_id=thread_id,
        user_id=request.user_id
    )
    
    return response

@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """Stream a chat response"""
    # Generate a thread_id if not provided
    thread_id = request.thread_id or str(uuid.uuid4())
    
    async def event_generator():
        # Use the streaming method of the agent
        for event_type, data in agent_service.stream_message(
            message_text=request.message,
            thread_id=thread_id,
            user_id=request.user_id
        ):
            # Format as server-sent event
            yield f"data: {json.dumps(data)}\n\n"
            
            # Allow other tasks to run
            await asyncio.sleep(0)
        
        # Send a final event with the thread_id
        yield f"data: {json.dumps({'done': True, 'thread_id': thread_id})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.post("/chat/system", response_model=ChatResponse)
async def chat_with_system_message(request: SystemMessageRequest):
    """Process a chat message with a custom system message"""
    # Generate a thread_id if not provided
    thread_id = request.thread_id or str(uuid.uuid4())
    
    # Send the message to the agent with the system message
    response = agent_service.send_message(
        message_text=request.message,
        thread_id=thread_id,
        user_id=request.user_id,
        system_message=request.system_message
    )
    
    return response

@router.post("/chat/system/stream")
async def stream_chat_with_system_message(request: SystemMessageRequest):
    """Stream a chat response with a custom system message"""
    # Generate a thread_id if not provided
    thread_id = request.thread_id or str(uuid.uuid4())
    
    async def event_generator():
        # Use the streaming method of the agent with the system message
        for event_type, data in agent_service.stream_message(
            message_text=request.message,
            thread_id=thread_id,
            user_id=request.user_id,
            system_message=request.system_message
        ):
            # Format as server-sent event
            yield f"data: {json.dumps(data)}\n\n"
            
            # Allow other tasks to run
            await asyncio.sleep(0)
        
        # Send a final event with the thread_id
        yield f"data: {json.dumps({'done': True, 'thread_id': thread_id})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """List all available agents"""
    return agent_service.get_available_agents()

@router.put("/agents/active/{agent_id}")
async def set_active_agent(agent_id: str):
    """Set the active agent"""
    success = agent_service.set_active_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    active = agent_service.active_agent
    return {"success": True, "active_agent": {
        "id": agent_id,
        "name": active.name,
        "description": active.description
    }}

@router.get("/threads")
async def get_threads(user_id: Optional[str] = None):
    """Get all threads, optionally filtered by user_id"""
    return agent_service.get_threads(user_id)

@router.get("/threads/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str):
    """Get a thread by ID"""
    thread = agent_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return thread

@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a thread"""
    success = agent_service.delete_thread(thread_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return {"success": True}
