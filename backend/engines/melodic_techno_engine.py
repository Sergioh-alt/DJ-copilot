"""
DJ Copilot AI — Melodic Techno Mixing Engine
Extremely long blends, careful EQ management to avoid synth clashing.
"""
from engines.base_engine import MixingEngine
from database.models import TrackFeatures, TransitionType


class MelodicTechnoEngine(MixingEngine):

    @property
    def name(self) -> str:
        return "Melodic Techno Engine"

    @property
    def mix_duration_bars(self) -> tuple:
        return (32, 64, 128)  # min, ideal, max

    @property
    def aggressiveness(self) -> float:
        return 0.1  # Very slow and smooth

    @property
    def preferred_transitions(self) -> list:
        return [TransitionType.PROGRESSIVE_BLEND, TransitionType.FILTER_SWEEP]

    def get_entry_point_bars(self, features: TrackFeatures) -> int:
        """Melodic Techno: Enter at the start of a long atmospheric section."""
        return 16

    def get_eq_strategy(self, features_a: TrackFeatures, features_b: TrackFeatures) -> list:
        """Melodic Techno EQ: Extremely slow progression, avoid mid clash."""
        actions = []
        actions.append("Corta LOWS y MIDS del Deck B casi por completo")
        actions.append("Filtro High-Pass (HPF) activado en el Deck B al entrar")
        actions.append("Libera el filtro y sube MIDS durante 32 compases")
        actions.append("Bass swap muy gradual en el compás 33")
        return actions

    def get_transition_type(self, features_a: TrackFeatures, features_b: TrackFeatures) -> TransitionType:
        return TransitionType.PROGRESSIVE_BLEND
