"""
DJ Copilot AI — Salsa Engine
Engine for Salsa and Tropical genres.
"""
from engines.base_engine import MixingEngine
from database.models import TrackFeatures, TransitionType


class SalsaEngine(MixingEngine):

    @property
    def name(self) -> str:
        return "Salsa"

    @property
    def mix_duration_bars(self) -> tuple:
        return (2, 4, 8)  # Quick transitions or on-phrase cuts

    @property
    def aggressiveness(self) -> float:
        return 0.8  # Cuts and swaps are common in tropical music

    @property
    def preferred_transitions(self) -> list:
        return [TransitionType.CUT, TransitionType.ECHO_OUT, TransitionType.SWAP]

    def get_entry_point_bars(self, features: TrackFeatures) -> int:
        return 32

    def get_eq_strategy(self, features_a: TrackFeatures, features_b: TrackFeatures) -> list:
        return [
            "cut_low_a", 
            "boost_high_b_slightly",
            "swap_lows_on_beat_1"
        ]

    def get_transition_type(self, features_a: TrackFeatures, features_b: TrackFeatures) -> TransitionType:
        if abs(features_a.bpm - features_b.bpm) > 5:
            return TransitionType.ECHO_OUT
        return TransitionType.CUT
