"""
DJ Copilot AI — Tech House Engine
Engine for Tech House.
"""
from engines.base_engine import MixingEngine
from database.models import TrackFeatures, TransitionType


class TechHouseEngine(MixingEngine):

    @property
    def name(self) -> str:
        return "Tech House"

    @property
    def mix_duration_bars(self) -> tuple:
        return (8, 16, 32)

    @property
    def aggressiveness(self) -> float:
        return 0.4

    @property
    def preferred_transitions(self) -> list:
        return [TransitionType.BASS_SWAP, TransitionType.PROGRESSIVE_BLEND]

    def get_entry_point_bars(self, features: TrackFeatures) -> int:
        return 32

    def get_eq_strategy(self, features_a: TrackFeatures, features_b: TrackFeatures) -> list:
        return [
            "cut_low_b_fully", 
            "blend_mids",
            "bass_swap_on_phrase"
        ]

    def get_transition_type(self, features_a: TrackFeatures, features_b: TrackFeatures) -> TransitionType:
        if features_a.energy > 0.7 and features_b.energy > 0.7:
            return TransitionType.BASS_SWAP
        return TransitionType.PROGRESSIVE_BLEND
