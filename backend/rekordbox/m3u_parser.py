"""
DJ Copilot AI — M3U8 Playlist Parser
Handles simple playlist imports for users who can't export XML.
"""
import os
from typing import List
from database.models import TrackModel, TrackFeatures

def parse_m3u8(file_path: str) -> List[TrackModel]:
    """Parse an .m3u or .m3u8 file and return a list of TrackModels."""
    tracks = []
    if not os.path.exists(file_path):
        return tracks

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # It's a file path
        audio_path = line
        if os.path.exists(audio_path):
            title = os.path.splitext(os.path.basename(audio_path))[0]
            
            track = TrackModel(
                title=title,
                artist="Unknown",
                file_path=audio_path,
                features=TrackFeatures(),
                analyzed=False
            )
            tracks.append(track)
            
    return tracks
