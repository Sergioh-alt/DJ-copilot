"""
DJ Copilot AI — Pydantic Data Models
Defines all data schemas used across the system.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class EngineType(str, Enum):
    TECHNO = "techno"
    REGGAETON = "reggaeton"
    HOUSE = "house"
    MELODIC_TECHNO = "melodic_techno"
    SALSA = "salsa"
    TECH_HOUSE = "tech_house"
    UNKNOWN = "unknown"


class TransitionType(str, Enum):
    PROGRESSIVE_BLEND = "progressive_blend"
    ECHO_OUT = "echo_out"
    CUT = "cut"
    SWAP = "swap"
    BASS_SWAP = "bass_swap"
    FILTER_SWEEP = "filter_sweep"


class AlertLevel(str, Enum):
    DANGER = "danger"      # 🔴
    WARNING = "warning"    # 🟡
    SAFE = "safe"          # 🟢


# ── Track Analysis Result ──
class TrackFeatures(BaseModel):
    bpm: float = 0.0
    key: str = "Unknown"
    camelot_code: str = "1A"
    energy: float = 0.0             # 0.0 - 1.0
    energy_curve: List[float] = Field(default_factory=list)
    bass_intensity: float = 0.0     # 0.0 - 1.0
    mid_intensity: float = 0.0
    high_intensity: float = 0.0
    vocal_presence: float = 0.0     # 0.0 - 1.0
    groove_density: float = 0.0     # 0.0 - 1.0
    drop_positions: List[float] = Field(default_factory=list)      # seconds
    breakdown_positions: List[float] = Field(default_factory=list)  # seconds
    phrase_length: float = 0.0      # beats
    duration: float = 0.0           # seconds
    spectral_centroid_mean: float = 0.0
    embedding: List[float] = Field(default_factory=list)  # 512-dim vector


class TrackModel(BaseModel):
    id: Optional[int] = None
    title: str = "Unknown"
    artist: str = "Unknown"
    file_path: str = ""
    features: Optional[TrackFeatures] = None
    assigned_engine: EngineType = EngineType.UNKNOWN
    user_corrected_engine: Optional[EngineType] = None
    rekordbox_id: Optional[str] = None
    analyzed: bool = False


class TrackResponse(BaseModel):
    id: int
    title: str
    artist: str
    bpm: float
    key: str
    camelot_code: str
    energy: float
    bass_intensity: float
    vocal_presence: float
    groove_density: float
    assigned_engine: str
    user_corrected_engine: Optional[str] = None
    duration: float
    analyzed: bool


# ── EQ Advice ──
class EQAlert(BaseModel):
    level: AlertLevel
    frequency_band: str     # "LOW", "MID", "HIGH"
    message: str
    action: str             # "cut_low_b", "reduce_mid_a", etc.
    value: Optional[float] = None  # suggested value 0.0-1.0


class EQAdvice(BaseModel):
    deck_a_track: str
    deck_b_track: str
    alerts: List[EQAlert] = Field(default_factory=list)
    overall_compatibility: float = 0.0  # 0.0 - 1.0


# ── Transition Suggestion ──
class TransitionSuggestion(BaseModel):
    transition_type: TransitionType
    entry_point_seconds: float
    entry_point_bars: int
    mix_duration_bars: int
    eq_actions: List[str] = Field(default_factory=list)
    engine_used: EngineType
    confidence: float = 0.0


# ── Affinity Link ──
class AffinityLink(BaseModel):
    track_a_id: int
    track_b_id: int
    harmonic_score: float = 0.0
    bpm_score: float = 0.0
    texture_score: float = 0.0
    engine_score: float = 0.0
    energy_flow_score: float = 0.0
    total_score: float = 0.0


class RecommendationResponse(BaseModel):
    track: TrackResponse
    affinity_score: float
    harmonic_match: str       # "perfect", "compatible", "energy_boost"
    transition: TransitionSuggestion


# ── Correction (RLHF) ──
class CorrectionRecord(BaseModel):
    track_id: int
    original_engine: EngineType
    corrected_engine: EngineType
    timestamp: Optional[str] = None
