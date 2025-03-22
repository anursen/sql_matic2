from fastapi import APIRouter
from .agent_routes import router as agent_router

router = APIRouter()
router.include_router(agent_router, prefix="/agent")
