"""
DJ Copilot AI — Night Programmer (Set Planner)
A* Pathfinding and Suggestion Engine.
"""
from typing import List, Dict, Any
from database import db_manager
from intelligence.affinity_graph import calculate_affinity
from engines import engine_router
from database.models import EngineType, TrackFeatures

class SetPlanner:
    def __init__(self):
        pass

    def get_track_options(self, current_track_id: int, target_track_id: int = None, limit: int = 5) -> List[Dict]:
        """
        Provides next track options. If target_track_id is provided, biases the search
        towards tracks that mathematically bridge the gap (A* heuristic).
        """
        # Fetch current track
        current_track = self._get_track(current_track_id)
        if not current_track:
            return []

        # Get top 20 affinities from DB
        affinities = db_manager.get_top_affinities(current_track_id, limit=20)
        options = []

        target_track = None
        if target_track_id:
            target_track = self._get_track(target_track_id)

        for aff in affinities:
            next_track_id = aff["track_b_id"] if aff["track_a_id"] == current_track_id else aff["track_a_id"]
            next_track = self._get_track(next_track_id)
            if not next_track:
                continue
            
            score = aff["total_score"]
            
            # A* Heuristic: If we have a target, we want to pick a next track that is 'closer' to the target
            if target_track:
                # Calculate direct heuristic distance between 'next_track' and 'target_track'
                # For a true A*, we would expand a tree. Here we do a greedy 1-step lookahead + heuristic.
                heuristic_bpm = 1.0 - (abs(next_track["bpm"] - target_track["bpm"]) / 10.0)
                heuristic_energy = 1.0 - abs(next_track["energy"] - target_track["energy"])
                h_score = max(0, (heuristic_bpm * 0.5) + (heuristic_energy * 0.5))
                score = (score * 0.6) + (h_score * 0.4)

            # Create a mock TrackFeatures object to avoid AttributeError
            feats = TrackFeatures(
                bpm=next_track.get("bpm", 128),
                key=next_track.get("key", "1A"),
                energy=next_track.get("energy", 0.5),
                bass_intensity=next_track.get("bass_intensity", 0.5),
                vocal_presence=next_track.get("vocal_presence", 0.5),
                groove_density=next_track.get("groove_density", 0.5),
                breakdown_positions=[],
                drop_positions=[]
            )

            # Generate mix points
            engine = engine_router.get_engine(engine_router.get_effective_engine(next_track.get("assigned_engine")))
            mix_bars = engine.mix_duration_bars[1]
            entry_point = engine.get_entry_point_bars(feats) * (60.0 / next_track["bpm"]) if next_track.get("bpm") else 30.0

            options.append({
                "track": next_track,
                "score": score,
                "mix_points": {
                    "entry_seconds": entry_point,
                    "mix_duration_bars": mix_bars,
                    "transition_type": engine.preferred_transitions[0].value
                }
            })

        # Sort by best score (including A* heuristic)
        options.sort(key=lambda x: x["score"], reverse=True)
        return options[:limit]

    def _get_track(self, track_id: int):
        tracks = db_manager.get_all_tracks()
        for t in tracks:
            if t["id"] == track_id:
                return t
        return None

planner_engine = SetPlanner()
