"""
DJ Copilot AI — House Mixing Engine
Groovy, 4/4 consistent blends, stab-based transitions.
"""
from engines.base_engine import MixingEngine
from database.models import TrackFeatures, TransitionType


class HouseEngine(MixingEngine):

    @property
    def name(self) -> str:
        return "House Engine"

    @property
    def mix_duration_bars(self) -> tuple:
        return (8, 16, 32)  # min, ideal, max

    @property
    def aggressiveness(self) -> float:
        return 0.4  # Moderate

    @property
    def preferred_transitions(self) -> list:
        return [TransitionType.PROGRESSIVE_BLEND, TransitionType.BASS_SWAP, TransitionType.CUT]

    def get_entry_point_bars(self, features: TrackFeatures) -> int:
        """House: Enter at phrase start (typically bar 8 or 16)."""
        return 8

    def get_eq_strategy(self, features_a: TrackFeatures, features_b: TrackFeatures) -> list:
        """House EQ: Clean mid transition, sharp bass swap on the downbeat."""
        actions = []
        actions.append("Corta LOWS del Deck B completamente")
        actions.append("Sube MIDS y HIGHS gradualmente en 8 compases")
        actions.append("Hace Bass Swap seco (Cut) en el inicio de frase (compás 9)")
        return actions

    def get_transition_type(self, features_a: TrackFeatures, features_b: TrackFeatures) -> TransitionType:
        return TransitionType.BASS_SWAP
