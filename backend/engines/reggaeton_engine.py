"""
DJ Copilot AI — Reggaetón/Urban Mixing Engine
Fast cuts, echo outs, vocal timing, immediate impact.
"""
from engines.base_engine import MixingEngine
from database.models import TrackFeatures, TransitionType


class ReggaetonEngine(MixingEngine):

    @property
    def name(self) -> str:
        return "Reggaetón Engine"

    @property
    def mix_duration_bars(self) -> tuple:
        return (2, 4, 8)  # Fast transitions

    @property
    def aggressiveness(self) -> float:
        return 0.8  # Very aggressive

    @property
    def preferred_transitions(self) -> list:
        return [TransitionType.ECHO_OUT, TransitionType.CUT, TransitionType.SWAP]

    def get_entry_point_bars(self, features: TrackFeatures) -> int:
        """Reggaetón: enter at the hook or first recognizable moment."""
        if features.drop_positions:
            bpm = features.bpm if features.bpm > 0 else 95
            first_drop = features.drop_positions[0]
            bars = int(first_drop / (60.0 / bpm * 4))
            return max(bars - 2, 1)  # 2 bars before the drop
        return 1  # Start almost immediately

    def get_eq_strategy(self, features_a: TrackFeatures, features_b: TrackFeatures) -> list:
        """Reggaetón EQ: aggressive, instant swap, protect vocals."""
        actions = []

        # Quick swap strategy
        actions.append("Echo Out del Deck A en el último compás")
        actions.append("Deck B entra con LOWS y MIDS al 100% inmediatamente")

        # Vocal protection
        if features_a.vocal_presence > 0.5 and features_b.vocal_presence > 0.5:
            actions.insert(0, "🔴 CONFLICTO VOCAL — Espera a que termine el hook del Deck A")
            actions.append("No mezcles vocales: corte seco después del hook")

        # Bass handling
        if features_b.bass_intensity > 0.5:
            actions.append("LOWS del Deck B al máximo para impacto inmediato")

        return actions

    def get_transition_type(self, features_a: TrackFeatures, features_b: TrackFeatures) -> TransitionType:
        """Reggaetón: echo out if vocals present, cut if not."""
        if features_a.vocal_presence > 0.4:
            return TransitionType.ECHO_OUT
        return TransitionType.CUT
