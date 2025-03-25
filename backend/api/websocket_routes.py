from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from ..services.chat_service import ChatService, get_chat_service
from ..websocket.handlers import get_websocket_manager
import logging
import json
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str,
    thread_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    chat_service: ChatService = Depends(get_chat_service)
):
    websocket_manager = get_websocket_manager(chat_service)
    await websocket_manager.connect(websocket, client_id, user_id, thread_id, agent_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "")
                
                if message_type == "chat_message":
                    await websocket_manager.handle_chat_message(client_id, message_data.get("payload", {}))
                elif message_type == "agent_message":
                    await websocket_manager.handle_agent_message(client_id, message_data.get("payload", {}))
                # Add other message type handlers as needed
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}: {data}")
                await websocket_manager.send_message(client_id, {
                    "type": "error",
                    "payload": {
                        "message": "Invalid message format"
                    }
                })
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
