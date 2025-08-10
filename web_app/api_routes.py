from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from models import (
    SourcesResponse, 
    SystemValidationResponse, 
    CharacterSummary,
    SessionHistoryResponse,
    ModelUpdateRequest,
    ModelResponse
)

router = APIRouter()

# Global variables to store dependencies - will be set by main.py
_engine = None
_session_manager = None

def set_dependencies(engine, session_manager):
    """Set the engine and session manager dependencies."""
    global _engine, _session_manager
    _engine = engine
    _session_manager = session_manager

def get_engine():
    """Dependency to get the engine instance."""
    if _engine is None:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    return _engine

def get_session_manager():
    """Dependency to get the session manager instance."""
    if _session_manager is None:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    return _session_manager

@router.get("/sources", response_model=SourcesResponse)
async def get_available_sources(engine=Depends(get_engine)):
    """Get available knowledge sources."""
    try:
        sources = engine.get_available_sources()
        return SourcesResponse(
            sources=sources,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate", response_model=SystemValidationResponse)
async def validate_system(engine=Depends(get_engine)):
    """Validate system health and data integrity."""
    try:
        # Check if engine is initialized
        if not engine:
            return SystemValidationResponse(
                status="error",
                message="Engine not initialized"
            )
        
        # Check knowledge base
        kb_status = engine.knowledge_base is not None
        
        # Check if we can access character data
        try:
            character_info = engine.knowledge_base.get_basic_character_info()
            character_status = bool(character_info)
        except:
            character_status = False
        
        return SystemValidationResponse(
            status="success" if kb_status and character_status else "partial",
            message="System validation complete",
            details={
                "knowledge_base": kb_status,
                "character_data": character_status,
                "engine": True
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/character", response_model=CharacterSummary)
async def get_character_summary(engine=Depends(get_engine)):
    """Get character summary information."""
    try:
        character_data = engine.knowledge_base.get_basic_character_info()
        
        if not character_data:
            raise HTTPException(status_code=404, detail="Character data not found")
        
        # Extract key information - character data is already flattened
        return CharacterSummary(
            name=character_data.get("name", "Unknown"),
            class_info=f"{character_data.get('class', 'Unknown')} {character_data.get('level', '?')}",
            race=character_data.get("race", "Unknown"),
            hit_points={
                "current": character_data.get("current_hp", 0),
                "max": character_data.get("max_hp", 0)
            },
            armor_class=character_data.get("armor_class", 0),
            key_stats=character_data.get("ability_scores", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-history/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str, session_manager=Depends(get_session_manager)):
    """Get session history for a specific session."""
    try:
        history = session_manager.get_session_history(session_id)
        return SessionHistoryResponse(
            session_id=session_id,
            history=history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", response_model=ModelResponse)
async def get_models(engine=Depends(get_engine)):
    """Get current model and available models."""
    try:
        return ModelResponse(
            current_model=engine.get_current_model(),
            available_models=engine.get_available_models(),
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models", response_model=ModelResponse)
async def update_model(request: ModelUpdateRequest, engine=Depends(get_engine)):
    """Update the OpenAI model used by the engine."""
    try:
        available_models = engine.get_available_models()
        if request.model not in available_models:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid model '{request.model}'. Available models: {available_models}"
            )
        
        engine.update_model(request.model)
        
        return ModelResponse(
            current_model=engine.get_current_model(),
            available_models=available_models,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
