"""
DJ Copilot AI — Affinity Graph (V2 with FAISS)
Pre-calculates compatibility between ALL tracks in the library.
Uses FAISS for sub-5ms vector search across thousands of tracks.
"""
import json
import numpy as np
import faiss
from typing import List
from audio.camelot import calculate_harmonic_score
from audio.feature_extractor import cosine_similarity
from database.models import AffinityLink, EngineType
from database import db_manager


# ── Affinity Weights ──
WEIGHT_HARMONIC = 0.35
WEIGHT_BPM = 0.20
WEIGHT_TEXTURE = 0.25
WEIGHT_ENGINE = 0.10
WEIGHT_ENERGY_FLOW = 0.10


def _bpm_score(bpm_a: float, bpm_b: float, max_diff: float = 4.0) -> float:
    if bpm_a <= 0 or bpm_b <= 0:
        return 0.0
    diff = abs(bpm_a - bpm_b)
    diff_half = abs(bpm_a - bpm_b * 2)
    diff_double = abs(bpm_a * 2 - bpm_b)
    effective_diff = min(diff, diff_half, diff_double)
    return max(0.0, 1.0 - (effective_diff / max_diff))


def _engine_score(engine_a: str, engine_b: str) -> float:
    if engine_a == engine_b:
        return 1.0
    return 0.3


def _energy_flow_score(energy_a: float, energy_b: float) -> float:
    diff = energy_b - energy_a
    if -0.1 <= diff <= 0.2:
        return 1.0
    elif diff > 0.2:
        return 0.7
    elif diff > -0.3:
        return 0.5
    else:
        return 0.2


def calculate_affinity(track_a: dict, track_b: dict, t_score: float) -> AffinityLink:
    """Calculate the affinity score between two tracks, using pre-computed texture score."""
    code_a = track_a.get("camelot_code", "1A")
    code_b = track_b.get("camelot_code", "1A")
    h_score, _ = calculate_harmonic_score(code_a, code_b)

    b_score = _bpm_score(track_a.get("bpm", 0), track_b.get("bpm", 0))

    eng_a = track_a.get("user_corrected_engine") or track_a.get("assigned_engine", "unknown")
    eng_b = track_b.get("user_corrected_engine") or track_b.get("assigned_engine", "unknown")
    e_score = _engine_score(eng_a, eng_b)

    ef_score = _energy_flow_score(track_a.get("energy", 0.5), track_b.get("energy", 0.5))

    total = (h_score * WEIGHT_HARMONIC +
             b_score * WEIGHT_BPM +
             t_score * WEIGHT_TEXTURE +
             e_score * WEIGHT_ENGINE +
             ef_score * WEIGHT_ENERGY_FLOW)

    return AffinityLink(
        track_a_id=track_a["id"],
        track_b_id=track_b["id"],
        harmonic_score=round(h_score, 3),
        bpm_score=round(b_score, 3),
        texture_score=round(t_score, 3),
        engine_score=round(e_score, 3),
        energy_flow_score=round(ef_score, 3),
        total_score=round(total, 3),
    )


def rebuild_affinity_graph():
    """
    Rebuild the entire affinity graph using FAISS for rapid vector similarity.
    """
    tracks = db_manager.get_all_tracks()
    analyzed = [t for t in tracks if t.get("analyzed")]

    if len(analyzed) < 2:
        return {"status": "need_more_tracks", "count": len(analyzed)}

    # Build FAISS Index (L2 distance equivalent to inner product for normalized vectors)
    dimension = 512
    index = faiss.IndexFlatIP(dimension)  # Inner Product
    
    embeddings = []
    track_mapping = []
    
    for t in analyzed:
        try:
            emb = json.loads(t.get("embedding", "[]"))
            if len(emb) == dimension:
                embeddings.append(emb)
                track_mapping.append(t)
        except:
            pass

    if len(embeddings) < 2:
        return {"status": "error_loading_embeddings"}

    emb_matrix = np.array(embeddings).astype('float32')
    index.add(emb_matrix)

    total_links = 0
    k = min(20, len(track_mapping))  # Get top 20 texture matches first to filter
    
    # Batch search
    distances, indices = index.search(emb_matrix, k)

    for i, track_a in enumerate(track_mapping):
        links = []
        for rank, j in enumerate(indices[i]):
            if i == j:  # skip self
                continue
            
            track_b = track_mapping[j]
            # Convert FAISS IP distance to cosine similarity score (0-1)
            t_score = float(np.clip((distances[i][rank] + 1) / 2.0, 0, 1))
            
            link = calculate_affinity(track_a, track_b, t_score)
            links.append(link)

        # Sort by total score and keep top 10
        links.sort(key=lambda x: x.total_score, reverse=True)
        for link in links[:10]:
            db_manager.insert_affinity_link(link)
            total_links += 1

    return {"status": "complete", "tracks_processed": len(track_mapping), "links_created": total_links}
