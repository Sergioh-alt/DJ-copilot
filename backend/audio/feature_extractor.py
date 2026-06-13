"""
DJ Copilot AI — Feature Extractor
Converts track features into a normalized numeric vector (embedding) for similarity search.
"""
import numpy as np
from database.models import TrackFeatures


def extract_embedding(features: TrackFeatures) -> list:
    """
    Create a 512-dimensional embedding vector from track features.
    This vector represents the musical "texture" of the track.
    For V1, we use a deterministic feature expansion. In V3, this will be a neural network.
    """
    # Core features (13 dimensions)
    core = np.array([
        features.bpm / 200.0,           # Normalized BPM (0-1)
        features.energy,
        features.bass_intensity,
        features.mid_intensity,
        features.high_intensity,
        features.vocal_presence,
        features.groove_density,
        features.phrase_length / 64.0,   # Normalized phrase length
        len(features.drop_positions) / 10.0,
        len(features.breakdown_positions) / 10.0,
        features.spectral_centroid_mean / 8000.0,
        features.duration / 600.0,       # Normalized duration (max ~10min)
        1.0 if features.vocal_presence > 0.5 else 0.0,  # Binary vocal flag
    ], dtype=np.float32)

    # Energy curve features (pad/truncate to 32 dims)
    ec = np.array(features.energy_curve[:32], dtype=np.float32)
    if len(ec) < 32:
        ec = np.pad(ec, (0, 32 - len(ec)), mode='constant')

    # Combine core + energy curve = 45 dims
    combined = np.concatenate([core, ec])

    # Expand to 512 dims using random projection (deterministic seed from features)
    seed = int(features.bpm * 100 + features.energy * 1000) % (2**31)
    rng = np.random.RandomState(seed)
    projection_matrix = rng.randn(len(combined), 512).astype(np.float32)
    embedding = combined @ projection_matrix

    # L2 normalize
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    return [round(float(x), 6) for x in embedding]


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Calculate cosine similarity between two embedding vectors."""
    if not vec_a or not vec_b:
        return 0.0
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.clip(dot / (norm_a * norm_b), -1, 1))
