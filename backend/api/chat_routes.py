from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional

from backend.models.data_models import (
    ChatThread,
    ChatMessage,
    ChatThreadList,
    CreateThreadRequest,
    AddMessageRequest,
    UpdateThreadTitleRequest
)
from backend.services.chat_service import ChatService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Create the router
router = APIRouter(prefix="/chat", tags=["chat"])

# Dependency to get the chat service
def get_chat_service():
    return ChatService()

@router.post("/threads", response_model=ChatThread)
async def create_thread(
    request: CreateThreadRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a new chat thread."""
    try:
        thread = await chat_service.create_thread(request)
        return thread
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads/user/{user_id}", response_model=Optional[str])
async def get_user_thread(
    user_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get the thread ID for a specific user."""
    try:
        thread_id = await chat_service.get_or_create_user_thread(user_id)
        return thread_id
    except Exception as e:
        logger.error(f"Error getting user thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads/{thread_id}", response_model=ChatThread)
async def get_thread(
    thread_id: str,
    with_messages: bool = True,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get a chat thread by ID."""
    try:
        thread = await chat_service.get_thread(thread_id, with_messages)
        if not thread:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        return thread
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads", response_model=ChatThreadList)
async def list_threads(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    chat_service: ChatService = Depends(get_chat_service)
):
    """List chat threads for a user."""
    try:
        thread_list = await chat_service.list_threads(user_id, page, page_size)
        return thread_list
    except Exception as e:
        logger.error(f"Error listing threads for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/threads/{thread_id}", response_model=bool)
async def delete_thread(
    thread_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Delete a chat thread."""
    try:
        success = await chat_service.delete_thread(thread_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        return success
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages", response_model=ChatMessage)
async def add_message(
    request: AddMessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Add a message to a thread."""
    try:
        # If no thread_id provided, get or create user's thread
        if not request.thread_id and request.user_id:
            thread_id = await chat_service.get_or_create_user_thread(request.user_id)
            request.thread_id = thread_id
            
        message = await chat_service.add_message(request)
        return message
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads/{thread_id}/messages", response_model=List[ChatMessage])
async def get_messages(
    thread_id: str,
    limit: int = Query(100, ge=1, le=1000),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get messages from a thread."""
    try:
        messages = await chat_service.get_messages(thread_id, limit)
        return messages
    except Exception as e:
        logger.error(f"Error getting messages for thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=ChatThreadList)
async def search_threads(
    user_id: str,
    query: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Search for threads by title or message content."""
    try:
        thread_list = await chat_service.search_threads(user_id, query, page, page_size)
        return thread_list
    except Exception as e:
        logger.error(f"Error searching threads for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/threads/{thread_id}/title", response_model=bool)
async def update_thread_title(
    thread_id: str,
    request: UpdateThreadTitleRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Update the title of a thread."""
    try:
        success = await chat_service.update_thread_title(thread_id, request.title)
        if not success:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        return success
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating title for thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
