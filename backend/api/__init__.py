from fastapi import APIRouter

# Create a router for all API endpoints
router = APIRouter()

# Import and include all route modules
from backend.api.chat_routes import router as chat_router
from .agent_routes import router as agent_router

# Include all routers
router.include_router(chat_router)
router.include_router(agent_router, prefix="/agent")
