from fastapi import APIRouter, HTTPException
from intelligence.night_programmer import planner_engine
from typing import Optional

router = APIRouter()

@router.get("/options")
def get_planner_options(current_id: int, target_id: Optional[int] = None, limit: int = 5):
    """
    Returns options to continue the set. 
    If target_id is provided, biases the options to build a bridge.
    """
    try:
        options = planner_engine.get_track_options(current_id, target_id, limit)
        return {"options": options}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
