"""
DJ Copilot AI — Base Mixing Engine
Abstract class that all specialized engines must implement.
"""
from abc import ABC, abstractmethod
from database.models import TrackFeatures, TransitionType


class MixingEngine(ABC):
    """
    Abstract base class for genre-specific mixing engines.
    Each engine defines mixing behavior, EQ strategy, transition types,
    and timing recommendations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine display name."""
        pass

    @property
    @abstractmethod
    def mix_duration_bars(self) -> tuple:
        """(min_bars, ideal_bars, max_bars) for transitions."""
        pass

    @property
    @abstractmethod
    def aggressiveness(self) -> float:
        """0.0 (smooth/gradual) to 1.0 (aggressive/instant)."""
        pass

    @property
    @abstractmethod
    def preferred_transitions(self) -> list:
        """List of TransitionType in order of preference."""
        pass

    @abstractmethod
    def get_entry_point_bars(self, features: TrackFeatures) -> int:
        """Calculate the ideal bar to start mixing in, based on track structure."""
        pass

    @abstractmethod
    def get_eq_strategy(self, features_a: TrackFeatures, features_b: TrackFeatures) -> list:
        """Return list of EQ action strings for the transition."""
        pass

    def get_transition_type(self, features_a: TrackFeatures, features_b: TrackFeatures) -> TransitionType:
        """Select the best transition type based on both tracks' features."""
        return self.preferred_transitions[0]
