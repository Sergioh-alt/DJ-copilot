"""
DJ Copilot AI — SQLite Database Manager
Handles all persistence: tracks, features, affinity links, and RLHF corrections.
"""
import sqlite3
import json
import os
from typing import List, Optional
from database.models import TrackModel, TrackFeatures, EngineType, AffinityLink, CorrectionRecord


DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data")
DB_PATH = os.path.join(DB_DIR, "copilot_master.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT 'Unknown',
            artist TEXT NOT NULL DEFAULT 'Unknown',
            file_path TEXT UNIQUE NOT NULL,
            bpm REAL DEFAULT 0.0,
            key_name TEXT DEFAULT 'Unknown',
            camelot_code TEXT DEFAULT '1A',
            energy REAL DEFAULT 0.0,
            energy_curve TEXT DEFAULT '[]',
            bass_intensity REAL DEFAULT 0.0,
            mid_intensity REAL DEFAULT 0.0,
            high_intensity REAL DEFAULT 0.0,
            vocal_presence REAL DEFAULT 0.0,
            groove_density REAL DEFAULT 0.0,
            drop_positions TEXT DEFAULT '[]',
            breakdown_positions TEXT DEFAULT '[]',
            phrase_length REAL DEFAULT 0.0,
            duration REAL DEFAULT 0.0,
            spectral_centroid_mean REAL DEFAULT 0.0,
            embedding TEXT DEFAULT '[]',
            assigned_engine TEXT DEFAULT 'unknown',
            user_corrected_engine TEXT DEFAULT NULL,
            rekordbox_id TEXT DEFAULT NULL,
            analyzed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS affinity_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_a_id INTEGER NOT NULL,
            track_b_id INTEGER NOT NULL,
            harmonic_score REAL DEFAULT 0.0,
            bpm_score REAL DEFAULT 0.0,
            texture_score REAL DEFAULT 0.0,
            engine_score REAL DEFAULT 0.0,
            energy_flow_score REAL DEFAULT 0.0,
            total_score REAL DEFAULT 0.0,
            FOREIGN KEY (track_a_id) REFERENCES tracks(id),
            FOREIGN KEY (track_b_id) REFERENCES tracks(id),
            UNIQUE(track_a_id, track_b_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            original_engine TEXT NOT NULL,
            corrected_engine TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (track_id) REFERENCES tracks(id)
        )
    """)

    conn.commit()
    conn.close()


def insert_track(track: TrackModel) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    features = track.features or TrackFeatures()
    try:
        cursor.execute("""
            INSERT INTO tracks (title, artist, file_path, bpm, key_name, camelot_code,
                energy, energy_curve, bass_intensity, mid_intensity, high_intensity,
                vocal_presence, groove_density, drop_positions, breakdown_positions,
                phrase_length, duration, spectral_centroid_mean, embedding,
                assigned_engine, user_corrected_engine, rekordbox_id, analyzed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            track.title, track.artist, track.file_path,
            features.bpm, features.key, features.camelot_code,
            features.energy, json.dumps(features.energy_curve),
            features.bass_intensity, features.mid_intensity, features.high_intensity,
            features.vocal_presence, features.groove_density,
            json.dumps(features.drop_positions), json.dumps(features.breakdown_positions),
            features.phrase_length, features.duration, features.spectral_centroid_mean,
            json.dumps(features.embedding),
            track.assigned_engine.value,
            track.user_corrected_engine.value if track.user_corrected_engine else None,
            track.rekordbox_id, 1 if track.analyzed else 0
        ))
        conn.commit()
        track_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Track already exists, update it
        cursor.execute("""
            UPDATE tracks SET title=?, artist=?, bpm=?, key_name=?, camelot_code=?,
                energy=?, energy_curve=?, bass_intensity=?, mid_intensity=?, high_intensity=?,
                vocal_presence=?, groove_density=?, drop_positions=?, breakdown_positions=?,
                phrase_length=?, duration=?, spectral_centroid_mean=?, embedding=?,
                assigned_engine=?, analyzed=?
            WHERE file_path=?
        """, (
            track.title, track.artist,
            features.bpm, features.key, features.camelot_code,
            features.energy, json.dumps(features.energy_curve),
            features.bass_intensity, features.mid_intensity, features.high_intensity,
            features.vocal_presence, features.groove_density,
            json.dumps(features.drop_positions), json.dumps(features.breakdown_positions),
            features.phrase_length, features.duration, features.spectral_centroid_mean,
            json.dumps(features.embedding),
            track.assigned_engine.value, 1 if track.analyzed else 0,
            track.file_path
        ))
        conn.commit()
        cursor.execute("SELECT id FROM tracks WHERE file_path=?", (track.file_path,))
        track_id = cursor.fetchone()["id"]
    conn.close()
    return track_id


def get_all_tracks() -> List[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tracks ORDER BY title").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_track_by_id(track_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM tracks WHERE id=?", (track_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_track_engine(track_id: int, engine: str):
    conn = get_connection()
    conn.execute("UPDATE tracks SET user_corrected_engine=? WHERE id=?", (engine, track_id))
    conn.commit()
    conn.close()


def delete_track(track_id: int):
    """Remove a track from the DB (but don't touch the file)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM affinity_links WHERE track_a_id=? OR track_b_id=?", (track_id, track_id))
    cursor.execute("DELETE FROM corrections WHERE track_id=?", (track_id,))
    cursor.execute("DELETE FROM tracks WHERE id=?", (track_id,))
    conn.commit()
    conn.close()



def insert_affinity_link(link: AffinityLink):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO affinity_links
                (track_a_id, track_b_id, harmonic_score, bpm_score,
                 texture_score, engine_score, energy_flow_score, total_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (link.track_a_id, link.track_b_id, link.harmonic_score,
              link.bpm_score, link.texture_score, link.engine_score,
              link.energy_flow_score, link.total_score))
        conn.commit()
    except Exception:
        pass
    conn.close()


def get_top_affinities(track_id: int, limit: int = 5) -> List[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT al.*, t.title, t.artist, t.bpm, t.key_name, t.camelot_code,
               t.energy, t.bass_intensity, t.vocal_presence, t.groove_density,
               t.assigned_engine, t.user_corrected_engine, t.duration, t.analyzed
        FROM affinity_links al
        JOIN tracks t ON t.id = al.track_b_id
        WHERE al.track_a_id = ?
        ORDER BY al.total_score DESC
        LIMIT ?
    """, (track_id, limit)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def insert_correction(correction: CorrectionRecord):
    conn = get_connection()
    conn.execute("""
        INSERT INTO corrections (track_id, original_engine, corrected_engine)
        VALUES (?, ?, ?)
    """, (correction.track_id, correction.original_engine.value,
          correction.corrected_engine.value))
    conn.commit()
    conn.close()


def get_corrections() -> List[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM corrections ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_all_data():
    """Wipe all tracks, links, and corrections. Start fresh."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM affinity_links")
    cursor.execute("DELETE FROM corrections")
    cursor.execute("DELETE FROM tracks")
    conn.commit()
    conn.close()

