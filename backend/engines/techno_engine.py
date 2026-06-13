"""
DJ Copilot AI — Techno Mixing Engine
Long progressive blends, gradual EQ, hypnotic continuity.
"""
from engines.base_engine import MixingEngine
from database.models import TrackFeatures, TransitionType


class TechnoEngine(MixingEngine):

    @property
    def name(self) -> str:
        return "Techno Engine"

    @property
    def mix_duration_bars(self) -> tuple:
        return (16, 32, 64)  # min, ideal, max

    @property
    def aggressiveness(self) -> float:
        return 0.2  # Very smooth

    @property
    def preferred_transitions(self) -> list:
        return [TransitionType.PROGRESSIVE_BLEND, TransitionType.BASS_SWAP, TransitionType.FILTER_SWEEP]

    def get_entry_point_bars(self, features: TrackFeatures) -> int:
        """Techno: enter at the start of a new 16-bar phrase, ideally after a breakdown."""
        if features.breakdown_positions:
            # Enter right after the first breakdown
            bpm = features.bpm if features.bpm > 0 else 128
            first_breakdown = features.breakdown_positions[0]
            bars = int(first_breakdown / (60.0 / bpm * 4))
            return max(bars, 8)
        # Default: enter at bar 8 (after 2 phrases)
        return 8

    def get_eq_strategy(self, features_a: TrackFeatures, features_b: TrackFeatures) -> list:
        """Techno EQ: gradual low-swap, keep mids clean."""
        actions = []

        # Always recommend gradual bass swap for techno
        actions.append("Corta LOWS del Deck B al 0% antes de entrar")
        actions.append("Sube LOWS del Deck B gradualmente en 16 compases")
        actions.append("Simultáneamente baja LOWS del Deck A")

        # If both have heavy bass, emphasize the swap
        if features_a.bass_intensity > 0.4 and features_b.bass_intensity > 0.4:
            actions.insert(0, "[WARN] Ambos tracks tienen graves pesados — Bass Swap obligatorio")

        # Mid handling
        if features_a.vocal_presence > 0.4 and features_b.vocal_presence > 0.4:
            actions.append("Reduce MIDS del Deck A al 50% para evitar conflicto vocal")

        # High frequencies
        actions.append("Mantén HIGHS de ambos decks para continuidad hipnótica")

        return actions

    def get_transition_type(self, features_a: TrackFeatures, features_b: TrackFeatures) -> TransitionType:
        """Select transition based on energy profiles."""
        # If incoming track has a strong drop, use filter sweep into it
        if features_b.drop_positions and features_b.energy > 0.7:
            return TransitionType.FILTER_SWEEP
        # Default: progressive blend
        return TransitionType.PROGRESSIVE_BLEND
