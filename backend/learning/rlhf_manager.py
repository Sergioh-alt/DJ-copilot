"""
DJ Copilot AI — RLHF Manager (Reinforcement Learning from Human Feedback)
Records user corrections and adjusts classification weights over time.
"""
from database.models import CorrectionRecord, EngineType
from database import db_manager


def record_correction(track_id: int, original_engine: str, corrected_engine: str):
    """Record a user correction for future learning."""
    correction = CorrectionRecord(
        track_id=track_id,
        original_engine=EngineType(original_engine),
        corrected_engine=EngineType(corrected_engine),
    )
    db_manager.insert_correction(correction)

    # Also update the track's user_corrected_engine
    db_manager.update_track_engine(track_id, corrected_engine)

    return {"status": "recorded", "track_id": track_id,
            "from": original_engine, "to": corrected_engine}


def get_correction_stats() -> dict:
    """
    Analyze correction history to understand user preferences.
    Returns stats on which engines get corrected most often.
    """
    corrections = db_manager.get_corrections()

    if not corrections:
        return {"total_corrections": 0, "patterns": []}

    # Count correction patterns
    pattern_counts = {}
    for c in corrections:
        key = f"{c['original_engine']} → {c['corrected_engine']}"
        pattern_counts[key] = pattern_counts.get(key, 0) + 1

    patterns = [{"pattern": k, "count": v} for k, v in
                sorted(pattern_counts.items(), key=lambda x: -x[1])]

    return {
        "total_corrections": len(corrections),
        "patterns": patterns,
    }
