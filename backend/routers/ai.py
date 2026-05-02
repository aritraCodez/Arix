"""
AI control endpoints.
Provides start/stop/status for the Gemini AI analyst session.
"""

import logging

from fastapi import APIRouter, HTTPException

from services.ai_analyst import get_ai_analyst

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Control"])


@router.post("/start")
async def start_ai():
    """Start or restart the AI analysis session."""
    analyst = get_ai_analyst()
    if analyst is None:
        raise HTTPException(status_code=503, detail="AI analyst not initialized")

    analyst.start_session()
    return {
        "status": "started",
        **analyst.get_status(),
    }


@router.post("/stop")
async def stop_ai():
    """Stop the AI analysis session."""
    analyst = get_ai_analyst()
    if analyst is None:
        raise HTTPException(status_code=503, detail="AI analyst not initialized")

    analyst.stop_session()
    return {
        "status": "stopped",
        **analyst.get_status(),
    }


@router.get("/status")
async def ai_status():
    """Get current AI analyst status."""
    analyst = get_ai_analyst()
    if analyst is None:
        return {
            "enabled": False,
            "available": False,
            "model": None,
            "session_minutes": 0,
            "session_remaining": None,
        }
    return analyst.get_status()


@router.post("/model")
async def set_model(model: str):
    """Change the default Gemini model."""
    analyst = get_ai_analyst()
    if analyst is None:
        raise HTTPException(status_code=503, detail="AI analyst not initialized")

    analyst.model = model
    logger.info(f"AI model changed to: {model}")
    return {
        "status": "model_updated",
        "model": model,
    }


@router.post("/session-duration")
async def set_session_duration(minutes: int):
    """Change the session duration (0 = unlimited)."""
    analyst = get_ai_analyst()
    if analyst is None:
        raise HTTPException(status_code=503, detail="AI analyst not initialized")

    analyst.session_minutes = max(0, minutes)
    logger.info(f"AI session duration set to: {'unlimited' if minutes == 0 else f'{minutes}min'}")
    return {
        "status": "duration_updated",
        "session_minutes": analyst.session_minutes,
    }
