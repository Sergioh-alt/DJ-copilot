"""
DJ Copilot AI — Rekordbox XML Parser
Reads exported rekordbox.xml files to import BPM, Key, Cues, and Playlists.
"""
import xml.etree.ElementTree as ET
from typing import List, Optional
from urllib.parse import unquote
from database.models import TrackModel, TrackFeatures


def parse_rekordbox_xml(xml_path: str) -> List[TrackModel]:
    """
    Parse a Rekordbox XML export file and return a list of TrackModel objects
    with basic metadata (BPM, Key, Cues, file path).
    """
    tracks = []

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except (ET.ParseError, FileNotFoundError) as e:
        print(f"Error parsing Rekordbox XML: {e}")
        return tracks

    # Rekordbox XML structure: DJ_PLAYLISTS > COLLECTION > TRACK
    collection = root.find(".//COLLECTION")
    if collection is None:
        return tracks

    for track_elem in collection.findall("TRACK"):
        attrs = track_elem.attrib

        # Extract basic metadata
        title = attrs.get("Name", "Unknown")
        artist = attrs.get("Artist", "Unknown")
        file_path = attrs.get("Location", "")
        rekordbox_id = attrs.get("TrackID", None)

        # BPM
        bpm = 0.0
        tempo_elem = track_elem.find("TEMPO")
        if tempo_elem is not None:
            bpm = float(tempo_elem.attrib.get("Bpm", "0"))
        elif "AverageBpm" in attrs:
            bpm = float(attrs.get("AverageBpm", "0"))

        # Key
        key_name = attrs.get("Tonality", "Unknown")

        # Duration
        duration = float(attrs.get("TotalTime", "0"))

        # Hot Cues
        cues = []
        for position_mark in track_elem.findall("POSITION_MARK"):
            cue_type = position_mark.attrib.get("Type", "0")
            cue_pos = float(position_mark.attrib.get("Start", "0"))
            cues.append({"type": cue_type, "position": cue_pos})

        # Normalize file path (Rekordbox uses file://localhost/ format)
        if file_path.startswith("file://localhost/"):
            file_path = file_path.replace("file://localhost/", "")
        
        # Decode URL characters like %20 for spaces
        file_path = unquote(file_path)
        
        file_path = file_path.replace("/", "\\") if "\\" not in file_path else file_path

        features = TrackFeatures(
            bpm=bpm,
            key=key_name,
            duration=duration,
        )

        track = TrackModel(
            title=title,
            artist=artist,
            file_path=file_path,
            features=features,
            rekordbox_id=rekordbox_id,
            analyzed=False,
        )
        tracks.append(track)

    return tracks


def extract_playlists(xml_path: str) -> dict:
    """Extract playlist structure from Rekordbox XML."""
    playlists = {}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except (ET.ParseError, FileNotFoundError):
        return playlists

    playlists_node = root.find(".//PLAYLISTS")
    if playlists_node is None:
        return playlists

    def _walk_node(node, path=""):
        for child in node.findall("NODE"):
            name = child.attrib.get("Name", "Untitled")
            node_type = child.attrib.get("Type", "0")
            current_path = f"{path}/{name}" if path else name

            if node_type == "1":  # Playlist
                track_ids = []
                for track in child.findall("TRACK"):
                    track_ids.append(track.attrib.get("Key", ""))
                playlists[current_path] = track_ids
            elif node_type == "0":  # Folder
                _walk_node(child, current_path)

    _walk_node(playlists_node)
    return playlists
