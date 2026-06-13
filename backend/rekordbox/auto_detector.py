"""
DJ Copilot AI — Auto Detector
Scans the system for Rekordbox XML files and audio directories.
Works on any PC — automatically finds music libraries.
"""
import os
import string
from typing import List, Dict


AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".m4a", ".ogg", ".wma"}

REKORDBOX_KNOWN_PATHS = [
    os.path.join(os.environ.get("APPDATA", ""), "Pioneer", "rekordbox"),
    os.path.join(os.environ.get("USERPROFILE", ""), "Documents"),
    os.path.join(os.environ.get("PUBLIC", ""), "Documents"),
    os.path.join(os.environ.get("APPDATA", ""), "Pioneer"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Pioneer", "rekordbox"),
]


def find_rekordbox_xml() -> List[str]:
    """
    Search common locations for rekordbox.xml files.
    Returns list of found XML paths.
    """
    found = []

    # Search known Rekordbox paths
    for base_path in REKORDBOX_KNOWN_PATHS:
        if not base_path or not os.path.exists(base_path):
            continue
        for root, dirs, files in os.walk(base_path):
            for f in files:
                if f.lower() in ("rekordbox.xml", "library.xml"):
                    found.append(os.path.join(root, f))
            # Don't go too deep
            if root.count(os.sep) - base_path.count(os.sep) > 3:
                dirs.clear()

    # Search root of all drives (Windows)
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if not os.path.exists(drive):
            continue
        # Check top-level only
        try:
            for item in os.listdir(drive):
                full_path = os.path.join(drive, item)
                if os.path.isfile(full_path) and item.lower() == "rekordbox.xml":
                    found.append(full_path)
        except PermissionError:
            continue

    return list(set(found))


def find_audio_directories(max_depth: int = 3) -> List[Dict]:
    """
    Find directories containing audio files across all drives.
    Returns list of {path, file_count, extensions}.
    """
    audio_dirs = []
    searched = set()

    # Common music folders
    user_profile = os.environ.get("USERPROFILE", "")
    search_roots = [
        os.path.join(user_profile, "Music"),
        os.path.join(user_profile, "Downloads"),
        os.path.join(user_profile, "Documents"),
    ]

    # Add all drive roots
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            search_roots.append(drive)

    for search_root in search_roots:
        if not os.path.exists(search_root) or search_root in searched:
            continue
        searched.add(search_root)

        try:
            for root, dirs, files in os.walk(search_root):
                depth = root.count(os.sep) - search_root.count(os.sep)
                if depth > max_depth:
                    dirs.clear()
                    continue

                audio_files = [f for f in files if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS]
                if len(audio_files) >= 3:  # At least 3 audio files
                    audio_dirs.append({
                        "path": root,
                        "file_count": len(audio_files),
                        "extensions": list(set(os.path.splitext(f)[1].lower() for f in audio_files)),
                    })

                # Skip hidden/system directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in
                           ("$recycle.bin", "windows", "program files", "program files (x86)",
                            "programdata", "node_modules", ".git")]
        except PermissionError:
            continue

    # Sort by file count (most files first)
    audio_dirs.sort(key=lambda x: x["file_count"], reverse=True)
    return audio_dirs[:50]  # Limit results


def scan_directory_for_audio(directory: str) -> List[str]:
    """Return all audio file paths in a directory (recursive)."""
    audio_files = []
    if not os.path.exists(directory):
        return audio_files

    for root, dirs, files in os.walk(directory):
        for f in files:
            if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS:
                audio_files.append(os.path.join(root, f))
        dirs[:] = [d for d in dirs if not d.startswith(".")]

    return audio_files
