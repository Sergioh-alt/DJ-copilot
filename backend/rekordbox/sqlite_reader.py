"""
DJ Copilot AI — Rekordbox SQLite Native Reader (V2)
Reads the native Rekordbox master.db directly to pull tracks instantly
without requiring the user to export XML.
"""
import os
import sqlite3
from typing import List
from database.models import TrackModel, TrackFeatures


def find_native_rekordbox_db() -> str:
    """Find the default path for Rekordbox 6+ master.db in Windows."""
    appdata = os.environ.get("APPDATA", "")
    db_path = os.path.join(appdata, "Pioneer", "rekordbox", "master.db")
    if os.path.exists(db_path):
        return db_path
    return ""


def parse_native_db(db_path: str) -> List[TrackModel]:
    """
    Connect to Rekordbox SQLite DB and extract all track metadata.
    NOTE: Rekordbox 6+ uses SQLCipher (encrypted). In a pure Python environment
    without pysqlcipher, this assumes an unencrypted backup or Rekordbox 5.
    If the DB is encrypted and fails, it returns an empty list (triggers XML fallback).
    """
    tracks = []
    
    if not db_path or not os.path.exists(db_path):
        return tracks

    try:
        # We attempt to connect. If it's encrypted with SQLCipher, standard sqlite3 will fail on execute.
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Read the djmdContent table (which holds track data)
        cursor.execute("SELECT * FROM djmdContent")
        rows = cursor.fetchall()
        
        for row in rows:
            # Reconstruct basic features from the DB row
            features = TrackFeatures(
                bpm=float(row["BPM"] / 100.0) if row["BPM"] else 0.0,
                key="Unknown", # Key ID mapping is required in real implementation
                duration=float(row["Duration"]) if row["Duration"] else 0.0,
            )
            
            track = TrackModel(
                title=row["Title"] or "Unknown",
                artist=row["ArtistName"] or "Unknown",
                file_path=row["FolderPath"] or "",
                features=features,
                rekordbox_id=str(row["ID"]),
                analyzed=False,
            )
            tracks.append(track)
            
        conn.close()
    except sqlite3.DatabaseError as e:
        # This will trigger if the database is encrypted (file is not a database)
        print(f"[Rekordbox Native] DB Error (possibly encrypted SQLCipher): {e}")
    except Exception as e:
        print(f"[Rekordbox Native] Error: {e}")
        
    return tracks
