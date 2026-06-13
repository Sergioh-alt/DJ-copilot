"""
DJ Copilot AI — Transition Advisor
Combines engine rules + EQ analysis to generate complete transition suggestions.
"""
from database.models import TransitionSuggestion, TrackFeatures, EngineType
from engines.engine_router import get_engine, get_effective_engine


def suggest_transition(track_a: dict, track_b: dict) -> TransitionSuggestion:
    """
    Generate a complete transition suggestion from Track A to Track B.
    Includes: entry point, transition type, duration, and EQ actions.
    """
    # Determine which engine to use (based on incoming track B)
    engine_type = get_effective_engine(
        track_b.get("assigned_engine", "unknown"),
        track_b.get("user_corrected_engine")
    )
    engine = get_engine(engine_type)

    # Build TrackFeatures for both tracks
    import json
    features_a = TrackFeatures(
        bpm=track_a.get("bpm", 0),
        key=track_a.get("key_name", "Unknown"),
        energy=track_a.get("energy", 0.5),
        bass_intensity=track_a.get("bass_intensity", 0.5),
        mid_intensity=track_a.get("mid_intensity", 0.3),
        high_intensity=track_a.get("high_intensity", 0.2),
        vocal_presence=track_a.get("vocal_presence", 0),
        groove_density=track_a.get("groove_density", 0.5),
        drop_positions=json.loads(track_a.get("drop_positions", "[]")),
        breakdown_positions=json.loads(track_a.get("breakdown_positions", "[]")),
        phrase_length=track_a.get("phrase_length", 16),
        duration=track_a.get("duration", 0),
    )
    features_b = TrackFeatures(
        bpm=track_b.get("bpm", 0),
        key=track_b.get("key_name", "Unknown"),
        energy=track_b.get("energy", 0.5),
        bass_intensity=track_b.get("bass_intensity", 0.5),
        mid_intensity=track_b.get("mid_intensity", 0.3),
        high_intensity=track_b.get("high_intensity", 0.2),
        vocal_presence=track_b.get("vocal_presence", 0),
        groove_density=track_b.get("groove_density", 0.5),
        drop_positions=json.loads(track_b.get("drop_positions", "[]")),
        breakdown_positions=json.loads(track_b.get("breakdown_positions", "[]")),
        phrase_length=track_b.get("phrase_length", 16),
        duration=track_b.get("duration", 0),
    )

    # Get engine recommendations
    transition_type = engine.get_transition_type(features_a, features_b)
    entry_bars = engine.get_entry_point_bars(features_b)
    eq_actions = engine.get_eq_strategy(features_a, features_b)
    _, ideal, _ = engine.mix_duration_bars

    # Calculate entry point in seconds
    bpm_b = features_b.bpm if features_b.bpm > 0 else 128
    entry_seconds = entry_bars * (60.0 / bpm_b * 4)  # bars to seconds

    return TransitionSuggestion(
        transition_type=transition_type,
        entry_point_seconds=round(entry_seconds, 2),
        entry_point_bars=entry_bars,
        mix_duration_bars=ideal,
        eq_actions=eq_actions,
        engine_used=engine_type,
        confidence=0.85,
    )
