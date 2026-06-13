"""
DJ Copilot AI — Engine Router
Classifies tracks and assigns the appropriate mixing engine based on audio features.
"""
from database.models import TrackFeatures, EngineType
from engines.base_engine import MixingEngine
from engines.techno_engine import TechnoEngine
from engines.reggaeton_engine import ReggaetonEngine
from engines.house_engine import HouseEngine
from engines.melodic_techno_engine import MelodicTechnoEngine
from engines.salsa_engine import SalsaEngine
from engines.tech_house_engine import TechHouseEngine


# Engine instances (singletons)
ENGINES = {
    EngineType.TECHNO: TechnoEngine(),
    EngineType.REGGAETON: ReggaetonEngine(),
    EngineType.HOUSE: HouseEngine(),
    EngineType.MELODIC_TECHNO: MelodicTechnoEngine(),
    EngineType.SALSA: SalsaEngine(),
    EngineType.TECH_HOUSE: TechHouseEngine(),
}


def classify_track(features: TrackFeatures) -> EngineType:
    """
    Rule-based classification of a track into a mixing engine.
    Uses BPM, groove density, vocal presence, and bass intensity.
    """
    bpm = features.bpm

    if 80 <= bpm <= 105 or 160 <= bpm <= 200:
        if features.groove_density > 0.8 and features.bass_intensity < 0.6:
            return EngineType.SALSA
        return EngineType.REGGAETON

    if 118 <= bpm <= 130:
        if features.groove_density > 0.6 and features.vocal_presence < 0.3:
            return EngineType.TECH_HOUSE if features.energy < 0.75 else EngineType.TECHNO
        elif features.energy < 0.6 and features.vocal_presence < 0.2:
            return EngineType.MELODIC_TECHNO
        else:
            return EngineType.HOUSE

    if 130 < bpm <= 150:
        if features.energy > 0.7:
            return EngineType.TECHNO
        else:
            return EngineType.MELODIC_TECHNO

    if 105 < bpm < 118:
        if features.vocal_presence > 0.4 or features.bass_intensity > 0.5:
            return EngineType.REGGAETON
        return EngineType.HOUSE

    return EngineType.TECHNO


def get_engine(engine_type: EngineType) -> MixingEngine:
    return ENGINES.get(engine_type, ENGINES[EngineType.TECHNO])


def get_effective_engine(assigned: str, user_corrected: str = None) -> EngineType:
    if user_corrected:
        try:
            return EngineType(user_corrected)
        except ValueError:
            pass
    try:
        return EngineType(assigned)
    except ValueError:
        return EngineType.UNKNOWN
